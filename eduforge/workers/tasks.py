"""
EduForge — Celery Workers
Async task queue for long-running ingestion, training and generation jobs.
Broker: Redis  |  Backend: Redis
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from celery import Celery
from celery.utils.log import get_task_logger

from core.config import settings
from core.utils import get_logger, utcnow, new_id

logger = get_logger("eduforge.workers")
task_logger = get_task_logger(__name__)

# ── Celery App ────────────────────────────────────────────────────────────────

celery_app = Celery(
    "eduforge",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "workers.tasks.ingest_material":  {"queue": "ingestion"},
        "workers.tasks.train_model":      {"queue": "training"},
        "workers.tasks.generate_exam":    {"queue": "generation"},
    },
    beat_schedule={
        "health-check-every-5min": {
            "task":     "workers.tasks.system_health_check",
            "schedule": 300.0,
        },
    },
)


# ── Task: Ingest Material ─────────────────────────────────────────────────────

@celery_app.task(
    name="workers.tasks.ingest_material",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def ingest_material(
    self,
    material_id: str,
    file_path: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Celery task: full ingestion pipeline for a document.
    Updates Material status in DB.
    """
    from core.database import SessionLocal
    from core.models import Material, MaterialStatus, Chunk
    from services.ingestion.pipeline import IngestionPipeline

    task_logger.info(f"[ingest_material] started material_id={material_id}")
    session = SessionLocal()

    try:
        mat = session.query(Material).filter(Material.id == material_id).first()
        if not mat:
            raise ValueError(f"Material {material_id} not found")

        mat.status = MaterialStatus.PROCESSING
        session.commit()

        pipeline = IngestionPipeline()
        chunks = pipeline.run(
            file_path=Path(file_path),
            material_id=material_id,
            metadata=metadata or {},
        )

        chunk_objs = [
            Chunk(
                id=c.get("vector_id", new_id()),
                material_id=material_id,
                content=c["content"],
                chunk_index=c["chunk_index"],
                vector_id=c.get("vector_id"),
                token_count=c.get("token_count", 0),
                metadata_=c.get("metadata", {}),
            )
            for c in chunks
        ]
        session.bulk_save_objects(chunk_objs)

        mat.status      = MaterialStatus.READY
        mat.chunk_count = len(chunks)
        mat.vector_ids  = [c.get("vector_id") for c in chunks]
        session.commit()

        task_logger.info(f"[ingest_material] complete material_id={material_id} chunks={len(chunks)}")
        return {"material_id": material_id, "chunks": len(chunks), "status": "ready"}

    except Exception as exc:
        task_logger.error(f"[ingest_material] failed: {exc}")
        session.query(Material).filter(Material.id == material_id).update(
            {"status": "failed"}
        )
        session.commit()
        raise self.retry(exc=exc)
    finally:
        session.close()


# ── Task: Train Model ─────────────────────────────────────────────────────────

@celery_app.task(
    name="workers.tasks.train_model",
    bind=True,
    max_retries=1,
    time_limit=7200,    # 2 hours max
    soft_time_limit=6900,
    acks_late=True,
)
def train_model(self, job_id: str) -> Dict[str, Any]:
    """Celery task: fine-tune model and log to MLflow."""
    from core.database import SessionLocal
    from core.models import TrainingJob, JobStatus, Chunk
    from services.training.trainer import EduModelTrainer, TrainingDataBuilder

    task_logger.info(f"[train_model] started job_id={job_id}")
    session = SessionLocal()

    try:
        job = session.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        if not job:
            raise ValueError(f"TrainingJob {job_id} not found")

        job.status     = JobStatus.RUNNING
        job.started_at = utcnow()
        session.commit()

        # Gather chunks
        chunks = []
        for mid in job.material_ids:
            db_chunks = session.query(Chunk).filter(Chunk.material_id == mid).all()
            chunks.extend([{"content": c.content, "chunk_index": c.chunk_index} for c in db_chunks])

        if not chunks:
            raise ValueError("No chunks found for given materials")

        builder = TrainingDataBuilder()
        records = builder.build_from_chunks(chunks)

        trainer = EduModelTrainer(base_model=job.base_model)
        result  = trainer.train(records, job_id=job_id, hyperparams=job.hyperparams)

        job.status         = JobStatus.COMPLETED
        job.finished_at    = utcnow()
        job.metrics        = result["metrics"]
        job.mlflow_run_id  = result["mlflow_run_id"]
        job.mlflow_run_url = result["mlflow_run_url"]
        job.model_artifact = result["model_path"]
        session.commit()

        task_logger.info(f"[train_model] complete job_id={job_id} metrics={result['metrics']}")
        return result

    except Exception as exc:
        task_logger.error(f"[train_model] failed: {exc}")
        job = session.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        if job:
            job.status        = JobStatus.FAILED
            job.error_message = str(exc)
            job.finished_at   = utcnow()
            session.commit()
        raise self.retry(exc=exc)
    finally:
        session.close()


# ── Task: Generate Exam ───────────────────────────────────────────────────────

@celery_app.task(
    name="workers.tasks.generate_exam",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    time_limit=1800,
    acks_late=True,
)
def generate_exam(self, job_id: str, exam_id: str) -> Dict[str, Any]:
    """Celery task: generate exam questions and persist them."""
    from core.database import SessionLocal
    from core.models import (
        GenerationJob, Exam, Question, QuestionType, DifficultyLevel, JobStatus
    )
    from services.generation.generator import ExamGenerator

    task_logger.info(f"[generate_exam] started job_id={job_id} exam_id={exam_id}")
    session = SessionLocal()

    try:
        job  = session.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        exam = session.query(Exam).filter(Exam.id == exam_id).first()
        if not job or not exam:
            raise ValueError("Job or Exam not found")

        job.status     = JobStatus.RUNNING
        job.started_at = utcnow()
        session.commit()

        cfg = job.config
        generator = ExamGenerator()
        questions = generator.generate_exam(
            material_ids=cfg["material_ids"],
            question_configs=cfg["question_configs"],
            topic=cfg.get("topic"),
        )

        q_objs = [
            Question(
                id=q.id,
                exam_id=exam_id,
                question_type=QuestionType(q.question_type),
                difficulty=DifficultyLevel(q.difficulty),
                content=q.content,
                options=q.options,
                correct_answer=q.correct_answer,
                explanation=q.explanation,
                rubric=q.rubric,
                points=q.points,
                order_index=q.order_index,
                raw_generation=q.raw_generation,
            )
            for q in questions
        ]
        session.bulk_save_objects(q_objs)

        job.status      = JobStatus.COMPLETED
        job.finished_at = utcnow()
        exam.num_questions = len(questions)
        session.commit()

        task_logger.info(f"[generate_exam] complete job_id={job_id} questions={len(questions)}")
        return {"exam_id": exam_id, "questions_generated": len(questions)}

    except Exception as exc:
        task_logger.error(f"[generate_exam] failed: {exc}")
        job = session.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if job:
            job.status        = JobStatus.FAILED
            job.error_message = str(exc)
            job.finished_at   = utcnow()
            session.commit()
        raise self.retry(exc=exc)
    finally:
        session.close()


# ── Task: System Health Check ─────────────────────────────────────────────────

@celery_app.task(name="workers.tasks.system_health_check")
def system_health_check() -> Dict[str, Any]:
    """Periodic health check — logs system status."""
    from core.database import health_check as db_health_check
    import redis as redis_lib

    db_ok = db_health_check()

    redis_ok = False
    try:
        r = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        redis_ok = bool(r.ping())
    except Exception:
        pass

    status = {"database": db_ok, "redis": redis_ok, "timestamp": utcnow().isoformat()}
    task_logger.info(f"[health_check] {status}")
    return status
