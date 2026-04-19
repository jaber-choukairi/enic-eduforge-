"""
EduForge — FastAPI Gateway
Single entry point exposing all REST endpoints.
Routers: /auth  /materials  /exams  /training  /jobs  /health
"""
from __future__ import annotations

import os
import shutil
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import redis
from fastapi import (
    BackgroundTasks, Depends, FastAPI, File, Form, HTTPException,
    Query, Security, UploadFile, status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.config import settings
from core.database import create_tables, get_db, health_check as db_health
from core.models import (
    Chunk, DifficultyLevel, Exam, ExamMaterial, GenerationJob,
    JobStatus, Material, MaterialStatus, Question, QuestionType,
    TrainingJob, User, UserRole,
)
from core.utils import (
    GenerationJobOut, ExamGenerateRequest, ExamOut, HealthResponse,
    MaterialCreate, MaterialOut, QuestionOut, TokenResponse,
    TrainingJobOut, TrainingRequest, UserCreate, UserOut,
    create_access_token, decode_access_token, hash_password,
    verify_password, get_logger, new_id, utcnow,
)

logger = get_logger("eduforge.gateway")

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered educational exam generation microservice",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bypass ngrok browser warning for all responses
@app.middleware("http")
async def add_ngrok_header(request, call_next):
    response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    logger.info("EduForge starting up", extra={"version": settings.APP_VERSION})
    create_tables()
    logger.info("Database tables ready")


# ── Auth Helpers ──────────────────────────────────────────────────────────────

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def require_teacher(user: User = Depends(get_current_user)) -> User:
    if user.role not in (UserRole.TEACHER, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Teacher or Admin role required")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health():
    db_ok = db_health()

    # Redis check
    redis_ok = False
    try:
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        redis_ok = r.ping()
    except Exception:
        pass

    # ChromaDB check — raw HTTP works with both v1 and v2 server APIs
    vector_ok = False
    try:
        import requests as _req
        for _path in ("/api/v2/heartbeat", "/api/v1/heartbeat"):
            try:
                _r = _req.get(
                    f"http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}{_path}",
                    timeout=2,
                )
                if _r.status_code == 200:
                    vector_ok = True
                    break
            except Exception:
                continue
    except Exception:
        pass

    overall = "healthy" if all([db_ok, redis_ok]) else "degraded"

    return HealthResponse(
        status=overall,
        version=settings.APP_VERSION,
        database=db_ok,
        redis=redis_ok,
        vector_db=vector_ok,
        timestamp=utcnow(),
    )


@app.get("/", tags=["system"])
async def root():
    return {"service": settings.APP_NAME, "version": settings.APP_VERSION, "docs": "/docs"}


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.post(f"{settings.API_PREFIX}/auth/register", response_model=UserOut, tags=["auth"])
async def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=409, detail="Username taken")

    user = User(
        id=new_id(),
        email=body.email,
        username=body.username,
        hashed_pw=hash_password(body.password),
        role=UserRole(body.role) if body.role in UserRole._value2member_map_ else UserRole.TEACHER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("User registered", extra={"user_id": user.id, "username": user.username})
    return user


@app.post(f"{settings.API_PREFIX}/auth/login", response_model=TokenResponse, tags=["auth"])
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_pw):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token({"sub": user.id, "role": user.role})
    logger.info("User logged in", extra={"user_id": user.id})
    return TokenResponse(access_token=token)


@app.get(f"{settings.API_PREFIX}/auth/me", response_model=UserOut, tags=["auth"])
async def me(user: User = Depends(get_current_user)):
    return user


# ── Materials ─────────────────────────────────────────────────────────────────

@app.post(f"{settings.API_PREFIX}/materials/upload", response_model=MaterialOut, tags=["materials"])
async def upload_material(
    title:       str        = Form(...),
    subject:     str        = Form(default=""),
    description: str        = Form(default=""),
    file:        UploadFile = File(...),
    background:  BackgroundTasks = BackgroundTasks(),
    user:        User       = Depends(require_teacher),
    db:          Session    = Depends(get_db),
):
    # Validate extension
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type {ext}. Allowed: {settings.SUPPORTED_EXTENSIONS}",
        )

    content = await file.read()
    size_kb = len(content) // 1024
    if size_kb > settings.MAX_FILE_SIZE_MB * 1024:
        raise HTTPException(status_code=413, detail="File too large")

    # Save file
    material_id = new_id()
    dest_dir = settings.UPLOAD_DIR / material_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / (file.filename or f"upload{ext}")
    dest_path.write_bytes(content)

    mat = Material(
        id=material_id,
        owner_id=user.id,
        title=title,
        description=description or None,
        subject=subject or None,
        file_path=str(dest_path),
        file_type=ext.lstrip("."),
        file_size_kb=size_kb,
        status=MaterialStatus.PENDING,
    )
    db.add(mat)
    db.commit()
    db.refresh(mat)

    # Trigger async ingestion
    background.add_task(_ingest_material_task, material_id, str(dest_path), db)

    logger.info("Material uploaded", extra={"material_id": material_id, "title": title})
    return mat


def _ingest_material_task(material_id: str, file_path: str, db: Session) -> None:
    """Background ingestion task (runs in FastAPI BackgroundTasks thread)."""
    from core.database import SessionLocal
    from services.ingestion.pipeline import IngestionPipeline

    session = SessionLocal()
    try:
        mat = session.query(Material).filter(Material.id == material_id).first()
        if not mat:
            return
        mat.status = MaterialStatus.PROCESSING
        session.commit()

        pipeline = IngestionPipeline()
        chunks = pipeline.run(
            file_path=Path(file_path),
            material_id=material_id,
            metadata={"subject": mat.subject or "", "title": mat.title},
        )

        # Persist chunks
        chunk_objs = []
        for c in chunks:
            chunk_objs.append(Chunk(
                id=c.get("vector_id", new_id()),
                material_id=material_id,
                content=c["content"],
                chunk_index=c["chunk_index"],
                vector_id=c.get("vector_id"),
                token_count=c.get("token_count", 0),
                metadata_=c.get("metadata", {}),
            ))
        session.bulk_save_objects(chunk_objs)

        mat.status = MaterialStatus.READY
        mat.chunk_count = len(chunks)
        mat.vector_ids = [c.get("vector_id") for c in chunks]
        session.commit()
        logger.info("Material ingested", extra={"material_id": material_id, "chunks": len(chunks)})

    except Exception as e:
        logger.error("Ingestion failed", extra={"material_id": material_id, "error": str(e)})
        session.query(Material).filter(Material.id == material_id).update(
            {"status": MaterialStatus.FAILED}
        )
        session.commit()
    finally:
        session.close()



@app.post(f"{settings.API_PREFIX}/materials/{{material_id}}/reprocess", response_model=MaterialOut, tags=["materials"])
async def reprocess_material(
    material_id: str,
    background: BackgroundTasks,
    user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Re-trigger ingestion for a material stuck in PENDING or FAILED state."""
    mat = db.query(Material).filter(
        Material.id == material_id, Material.owner_id == user.id
    ).first()
    if not mat:
        raise HTTPException(status_code=404, detail="Material not found")
    if mat.status == MaterialStatus.PROCESSING:
        raise HTTPException(status_code=409, detail="Material is already being processed")

    # Reset state
    mat.status = MaterialStatus.PENDING
    mat.chunk_count = 0
    db.commit()
    db.refresh(mat)

    background.add_task(_ingest_material_task, material_id, mat.file_path, db)
    logger.info("Reprocess triggered", extra={"material_id": material_id})
    return mat


@app.get(f"{settings.API_PREFIX}/materials", response_model=List[MaterialOut], tags=["materials"])
async def list_materials(
    skip:    int     = Query(0, ge=0),
    limit:   int     = Query(20, ge=1, le=100),
    subject: Optional[str] = Query(None),
    user:    User    = Depends(get_current_user),
    db:      Session = Depends(get_db),
):
    q = db.query(Material).filter(Material.owner_id == user.id)
    if subject:
        q = q.filter(Material.subject.ilike(f"%{subject}%"))
    return q.offset(skip).limit(limit).all()


@app.get(f"{settings.API_PREFIX}/materials/{{material_id}}", response_model=MaterialOut, tags=["materials"])
async def get_material(
    material_id: str,
    user: User = Depends(get_current_user),
    db:   Session = Depends(get_db),
):
    mat = db.query(Material).filter(
        Material.id == material_id, Material.owner_id == user.id
    ).first()
    if not mat:
        raise HTTPException(status_code=404, detail="Material not found")
    return mat


@app.delete(f"{settings.API_PREFIX}/materials/{{material_id}}", tags=["materials"])
async def delete_material(
    material_id: str,
    user: User    = Depends(require_teacher),
    db:   Session = Depends(get_db),
):
    mat = db.query(Material).filter(
        Material.id == material_id, Material.owner_id == user.id
    ).first()
    if not mat:
        raise HTTPException(status_code=404, detail="Material not found")

    # Remove from vector store
    try:
        from services.ingestion.pipeline import VectorStore
        vs = VectorStore()
        vs.delete_by_material(material_id)
    except Exception as e:
        logger.warning("Vector delete failed", extra={"error": str(e)})

    # Remove file
    if mat.file_path and Path(mat.file_path).exists():
        shutil.rmtree(Path(mat.file_path).parent, ignore_errors=True)

    db.delete(mat)
    db.commit()
    return {"message": "Material deleted", "id": material_id}


# ── Exams ─────────────────────────────────────────────────────────────────────

@app.post(f"{settings.API_PREFIX}/exams/generate", response_model=GenerationJobOut, tags=["exams"])
async def generate_exam(
    body:       ExamGenerateRequest,
    background: BackgroundTasks,
    user:       User    = Depends(require_teacher),
    db:         Session = Depends(get_db),
):
    # Validate materials exist and are ready
    for mid in body.material_ids:
        mat = db.query(Material).filter(Material.id == mid).first()
        if not mat:
            raise HTTPException(status_code=404, detail=f"Material {mid} not found")
        if mat.status != MaterialStatus.READY:
            raise HTTPException(
                status_code=422,
                detail=f"Material {mid} is not ready (status: {mat.status})"
            )

    # Create exam record
    total_q = sum(qc.count for qc in body.question_configs)
    exam = Exam(
        id=new_id(),
        creator_id=user.id,
        title=body.title,
        description=body.description,
        topic=body.topic,
        num_questions=total_q,
        time_limit_min=body.time_limit_min,
        instructions=body.instructions,
        generation_cfg={
            "question_configs": [qc.dict() for qc in body.question_configs],
            "material_ids": body.material_ids,
        },
    )
    db.add(exam)
    db.flush()

    # Link materials
    for mid in body.material_ids:
        db.add(ExamMaterial(exam_id=exam.id, material_id=mid))

    # Create generation job
    gen_job = GenerationJob(
        id=new_id(),
        created_by=user.id,
        exam_id=exam.id,
        status=JobStatus.QUEUED,
        config={
            "material_ids": body.material_ids,
            "question_configs": [qc.dict() for qc in body.question_configs],
            "topic": body.topic,
        },
    )
    db.add(gen_job)
    db.commit()
    db.refresh(gen_job)

    background.add_task(_generate_exam_task, gen_job.id, exam.id)

    logger.info(
        "Exam generation queued",
        extra={"exam_id": exam.id, "job_id": gen_job.id, "questions": total_q},
    )
    return gen_job


def _generate_exam_task(job_id: str, exam_id: str) -> None:
    from core.database import SessionLocal
    from services.generation.generator import ExamGenerator, AnthropicGenerator
    # Reset singleton so it picks up any env changes
    AnthropicGenerator._instance = None

    session = SessionLocal()
    try:
        job  = session.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        exam = session.query(Exam).filter(Exam.id == exam_id).first()
        if not job or not exam:
            return

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

        # Persist questions
        q_objs = []
        for q in questions:
            q_objs.append(Question(
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
            ))
        session.bulk_save_objects(q_objs)

        job.status      = JobStatus.COMPLETED
        job.finished_at = utcnow()
        exam.num_questions = len(questions)
        session.commit()

        logger.info(
            "Exam generated",
            extra={"exam_id": exam_id, "questions": len(questions)},
        )
    except Exception as e:
        logger.error("Exam generation task failed", extra={"job_id": job_id, "error": str(e)})
        if job:
            job.status        = JobStatus.FAILED
            job.error_message = str(e)
            job.finished_at   = utcnow()
            session.commit()
    finally:
        session.close()


@app.get(f"{settings.API_PREFIX}/exams", response_model=List[ExamOut], tags=["exams"])
async def list_exams(
    skip:  int     = Query(0, ge=0),
    limit: int     = Query(20, ge=1, le=100),
    user:  User    = Depends(get_current_user),
    db:    Session = Depends(get_db),
):
    exams = (
        db.query(Exam)
        .filter(Exam.creator_id == user.id)
        .offset(skip).limit(limit).all()
    )
    return exams


@app.get(f"{settings.API_PREFIX}/exams/{{exam_id}}", response_model=ExamOut, tags=["exams"])
async def get_exam(
    exam_id: str,
    user:    User    = Depends(get_current_user),
    db:      Session = Depends(get_db),
):
    exam = db.query(Exam).filter(
        Exam.id == exam_id, Exam.creator_id == user.id
    ).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam


@app.get(f"{settings.API_PREFIX}/exams/{{exam_id}}/export/markdown", tags=["exams"])
async def export_exam_markdown(
    exam_id:      str,
    student_view: bool   = Query(False),
    user:         User   = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    from services.generation.generator import ExamExporter, GeneratedQuestion
    exam = db.query(Exam).filter(
        Exam.id == exam_id, Exam.creator_id == user.id
    ).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    qs = db.query(Question).filter(Question.exam_id == exam_id).order_by(Question.order_index).all()
    gen_qs = [
        GeneratedQuestion(
            id=q.id,
            question_type=q.question_type.value,
            difficulty=q.difficulty.value,
            content=q.content,
            options=q.options,
            correct_answer=q.correct_answer,
            explanation=q.explanation,
            rubric=q.rubric,
            points=q.points,
            order_index=q.order_index,
        )
        for q in qs
    ]

    exporter = ExamExporter()
    if student_view:
        md = exporter.to_student_view(exam.title, gen_qs)
    else:
        md = exporter.to_markdown(exam.title, gen_qs)

    return PlainTextResponse(content=md, media_type="text/markdown")


@app.delete(f"{settings.API_PREFIX}/exams/{{exam_id}}", tags=["exams"])
async def delete_exam(
    exam_id: str,
    user: User    = Depends(require_teacher),
    db:   Session = Depends(get_db),
):
    exam = db.query(Exam).filter(
        Exam.id == exam_id, Exam.creator_id == user.id
    ).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    db.delete(exam)
    db.commit()
    return {"message": "Exam deleted", "id": exam_id}


# ── Training ──────────────────────────────────────────────────────────────────

@app.post(f"{settings.API_PREFIX}/training/start", response_model=TrainingJobOut, tags=["training"])
async def start_training(
    body:       TrainingRequest,
    background: BackgroundTasks,
    user:       User    = Depends(require_teacher),
    db:         Session = Depends(get_db),
):
    for mid in body.material_ids:
        mat = db.query(Material).filter(Material.id == mid).first()
        if not mat or mat.status != MaterialStatus.READY:
            raise HTTPException(status_code=422, detail=f"Material {mid} not ready")

    job = TrainingJob(
        id=new_id(),
        created_by=user.id,
        status=JobStatus.QUEUED,
        model_name=body.model_name,
        base_model=body.base_model,
        material_ids=body.material_ids,
        hyperparams=body.hyperparams,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background.add_task(_training_task, job.id)

    logger.info("Training job queued", extra={"job_id": job.id})
    return job


def _training_task(job_id: str) -> None:
    from core.database import SessionLocal
    from services.training.trainer import EduModelTrainer, TrainingDataBuilder

    session = SessionLocal()
    try:
        job = session.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        if not job:
            return

        job.status     = JobStatus.RUNNING
        job.started_at = utcnow()
        session.commit()

        # Gather chunks from DB
        chunks = []
        for mid in job.material_ids:
            db_chunks = session.query(Chunk).filter(Chunk.material_id == mid).all()
            chunks.extend([{"content": c.content, "chunk_index": c.chunk_index} for c in db_chunks])

        if not chunks:
            raise ValueError("No chunks found for training")

        builder = TrainingDataBuilder()
        records = builder.build_from_chunks(chunks)

        trainer = EduModelTrainer(base_model=job.base_model)
        result  = trainer.train(records, job_id=job_id, hyperparams=job.hyperparams)

        job.status          = JobStatus.COMPLETED
        job.finished_at     = utcnow()
        job.metrics         = result["metrics"]
        job.mlflow_run_id   = result["mlflow_run_id"]
        job.mlflow_run_url  = result["mlflow_run_url"]
        job.model_artifact  = result["model_path"]
        session.commit()

        logger.info("Training complete", extra={"job_id": job_id, "metrics": result["metrics"]})

    except Exception as e:
        logger.error("Training task failed", extra={"job_id": job_id, "error": str(e)})
        job = session.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        if job:
            job.status        = JobStatus.FAILED
            job.error_message = str(e)
            job.finished_at   = utcnow()
            session.commit()
    finally:
        session.close()


@app.get(f"{settings.API_PREFIX}/training", response_model=List[TrainingJobOut], tags=["training"])
async def list_training_jobs(
    skip:  int     = Query(0, ge=0),
    limit: int     = Query(20, ge=1, le=100),
    user:  User    = Depends(get_current_user),
    db:    Session = Depends(get_db),
):
    return (
        db.query(TrainingJob)
        .filter(TrainingJob.created_by == user.id)
        .offset(skip).limit(limit).all()
    )


@app.get(f"{settings.API_PREFIX}/training/{{job_id}}", response_model=TrainingJobOut, tags=["training"])
async def get_training_job(
    job_id: str,
    user:   User    = Depends(get_current_user),
    db:     Session = Depends(get_db),
):
    job = db.query(TrainingJob).filter(
        TrainingJob.id == job_id, TrainingJob.created_by == user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    return job


# ── Generation Jobs ───────────────────────────────────────────────────────────

@app.get(f"{settings.API_PREFIX}/jobs", response_model=List[GenerationJobOut], tags=["jobs"])
async def list_generation_jobs(
    skip:  int     = Query(0, ge=0),
    limit: int     = Query(20, ge=1, le=100),
    user:  User    = Depends(get_current_user),
    db:    Session = Depends(get_db),
):
    return (
        db.query(GenerationJob)
        .filter(GenerationJob.created_by == user.id)
        .offset(skip).limit(limit).all()
    )


@app.get(f"{settings.API_PREFIX}/jobs/{{job_id}}", response_model=GenerationJobOut, tags=["jobs"])
async def get_generation_job(
    job_id: str,
    user:   User    = Depends(get_current_user),
    db:     Session = Depends(get_db),
):
    job = db.query(GenerationJob).filter(
        GenerationJob.id == job_id, GenerationJob.created_by == user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job