"""
EduForge — CLI Utility Script
Usage:
  python scripts/cli.py setup          # create DB tables + seed demo user
  python scripts/cli.py seed           # insert demo material + exam
  python scripts/cli.py status         # check all services
  python scripts/cli.py ingest <file>  # manually ingest a file
  python scripts/cli.py generate       # run a test generation
  python scripts/cli.py reset-db       # drop & recreate all tables (dev only)
"""
import os
import sys

# ── Pre-load environment so pydantic-settings picks up .env correctly ─────────
# Find .env in the project root (parent of scripts/)
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
_env_path = os.path.join(_root, ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())

# Ensure project root is on PYTHONPATH
if _root not in sys.path:
    sys.path.insert(0, _root)


from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# ── Add project root to path ──────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("DATABASE_URL", "postgresql://eduforge:eduforge@localhost:5432/eduforge")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CHROMA_HOST", "localhost")
os.environ.setdefault("CHROMA_PORT", "8100")
os.environ.setdefault("MLFLOW_TRACKING_URI", "http://localhost:5000")

from core.config import settings
from core.utils import get_logger, hash_password, new_id

logger = get_logger("eduforge.cli")


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_setup(args):
    """Create DB tables and a default admin user."""
    print("🔧 Setting up EduForge...")

    from core.database import create_tables, SessionLocal
    from core.models import User, UserRole

    create_tables()
    print("✅ Database tables created")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if not existing:
            admin = User(
                id=new_id(),
                email="admin@eduforge.local",
                username="admin",
                hashed_pw=hash_password("admin123"),
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)

            teacher = User(
                id=new_id(),
                email="teacher@eduforge.local",
                username="teacher",
                hashed_pw=hash_password("teacher123"),
                role=UserRole.TEACHER,
                is_active=True,
            )
            db.add(teacher)
            db.commit()
            print("✅ Demo users created:")
            print("   admin / admin123")
            print("   teacher / teacher123")
        else:
            print("ℹ️  Admin user already exists")
    finally:
        db.close()

    print("\n🎉 Setup complete! Start the API with:")
    print("   uvicorn services.gateway.main:app --reload --host 0.0.0.0 --port 8000")


def cmd_seed(args):
    """Create a demo material and generate a test exam."""
    print("🌱 Seeding demo data...")

    demo_text = """
Introduction to Machine Learning

Machine learning is a branch of artificial intelligence that focuses on building systems 
that learn from data and improve their performance over time without being explicitly programmed.

Types of Machine Learning:

1. Supervised Learning
Supervised learning uses labeled training data to learn a mapping from inputs to outputs.
Common algorithms include linear regression for continuous outputs and logistic regression 
for classification tasks. Decision trees and random forests are also widely used.
Support Vector Machines (SVMs) are powerful for both classification and regression.

2. Unsupervised Learning
Unsupervised learning finds hidden patterns in data without labeled examples.
Clustering algorithms like K-Means group similar data points together.
Principal Component Analysis (PCA) reduces the dimensionality of data.
Autoencoders learn compressed representations of input data.

3. Reinforcement Learning
Reinforcement learning trains agents to make decisions by rewarding desired behaviors.
The agent interacts with an environment, takes actions, and receives rewards or penalties.
Q-Learning and Deep Q-Networks (DQN) are popular reinforcement learning algorithms.

Neural Networks and Deep Learning:

Neural networks are computational models inspired by the human brain.
They consist of layers of interconnected nodes called neurons.
Deep learning uses multiple hidden layers to learn complex representations.
Convolutional Neural Networks (CNNs) excel at image recognition tasks.
Recurrent Neural Networks (RNNs) and LSTMs handle sequential data like text.
Transformers have revolutionised natural language processing tasks.

Key Concepts:

- Training: The process of adjusting model parameters using data
- Overfitting: When a model learns training data too well and fails on new data
- Regularisation: Techniques to prevent overfitting (L1, L2, dropout)
- Cross-validation: Method to evaluate model performance reliably
- Gradient Descent: Optimisation algorithm for minimising loss functions
- Backpropagation: Algorithm for computing gradients in neural networks
- Hyperparameters: Settings that control the learning process
- Batch Normalisation: Technique to stabilise and speed up training

Applications of Machine Learning:
- Image and speech recognition
- Natural language processing and translation
- Recommendation systems
- Medical diagnosis
- Autonomous vehicles
- Financial fraud detection
- Climate modelling
"""

    # Write demo file
    demo_path = Path(settings.UPLOAD_DIR) / "demo_ml_lesson.txt"
    demo_path.parent.mkdir(parents=True, exist_ok=True)
    demo_path.write_text(demo_text.strip(), encoding="utf-8")
    print(f"✅ Demo material written to: {demo_path}")

    # Try to ingest via pipeline
    try:
        from core.database import SessionLocal
        from core.models import Material, MaterialStatus, Chunk, User
        from services.ingestion.pipeline import IngestionPipeline

        db = SessionLocal()
        teacher = db.query(User).filter(User.username == "teacher").first()
        if not teacher:
            print("⚠️  Run 'setup' first to create demo users")
            db.close()
            return

        mat_id = new_id()
        mat = Material(
            id=mat_id,
            owner_id=teacher.id,
            title="Introduction to Machine Learning",
            description="A comprehensive overview of ML concepts",
            subject="Computer Science",
            file_path=str(demo_path),
            file_type="txt",
            file_size_kb=len(demo_text) // 1024 + 1,
            status=MaterialStatus.PROCESSING,
        )
        db.add(mat)
        db.commit()
        print(f"✅ Material record created: {mat_id}")

        print("🔄 Running ingestion pipeline...")
        pipeline = IngestionPipeline()
        chunks = pipeline.run(
            file_path=demo_path,
            material_id=mat_id,
            metadata={"subject": "Computer Science"},
        )

        for c in chunks:
            db.add(Chunk(
                id=c.get("vector_id", new_id()),
                material_id=mat_id,
                content=c["content"],
                chunk_index=c["chunk_index"],
                vector_id=c.get("vector_id"),
                token_count=c.get("token_count", 0),
            ))

        mat.status = MaterialStatus.READY
        mat.chunk_count = len(chunks)
        db.commit()
        db.close()

        print(f"✅ Ingested {len(chunks)} chunks")
        print(f"\n📋 Material ID: {mat_id}")
        print("   Use this ID to generate an exam via the API or UI")

    except Exception as e:
        print(f"⚠️  Ingestion failed (ChromaDB may not be running): {e}")
        print("   You can still use the API to upload and process files when services are up")


def cmd_status(args):
    """Check the health of all dependent services."""
    print("🏥 EduForge Service Status\n")

    checks = []

    # Database
    try:
        from core.database import health_check
        ok = health_check()
        checks.append(("PostgreSQL", ok, "localhost:5432"))
    except Exception as e:
        checks.append(("PostgreSQL", False, str(e)[:50]))

    # Redis
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        ok = bool(r.ping())
        checks.append(("Redis", ok, settings.REDIS_URL))
    except Exception as e:
        checks.append(("Redis", False, str(e)[:50]))

    # ChromaDB
    try:
        import chromadb
        client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
        client.heartbeat()
        count = client.get_or_create_collection(settings.CHROMA_COLLECTION_NAME).count()
        checks.append(("ChromaDB", True, f"{count} vectors stored"))
    except Exception as e:
        checks.append(("ChromaDB", False, str(e)[:50]))

    # MLflow
    try:
        import mlflow
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        client = mlflow.tracking.MlflowClient()
        experiments = client.search_experiments()
        checks.append(("MLflow", True, f"{len(experiments)} experiments"))
    except Exception as e:
        checks.append(("MLflow", False, str(e)[:50]))

    # API
    try:
        import requests
        r = requests.get("http://localhost:8000/health", timeout=3)
        ok = r.status_code == 200
        checks.append(("API Gateway", ok, "http://localhost:8000"))
    except Exception as e:
        checks.append(("API Gateway", False, "Not running"))

    # Print results
    for name, ok, detail in checks:
        icon = "✅" if ok else "❌"
        status = "OK" if ok else "FAIL"
        print(f"  {icon} {name:<20} {status:<8} {detail}")

    print()
    all_ok = all(ok for _, ok, _ in checks)
    if all_ok:
        print("🎉 All services healthy!")
    else:
        failed = [n for n, ok, _ in checks if not ok]
        print(f"⚠️  Services down: {', '.join(failed)}")
        print("   Run: docker compose up -d")


def cmd_ingest(args):
    """Manually ingest a file."""
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return

    print(f"🔄 Ingesting: {file_path}")
    try:
        from services.ingestion.pipeline import IngestionPipeline
        pipeline = IngestionPipeline()
        mat_id = new_id()
        chunks = pipeline.run(file_path=file_path, material_id=mat_id)
        print(f"✅ Ingested {len(chunks)} chunks (material_id: {mat_id})")
        for i, c in enumerate(chunks[:3]):
            print(f"   Chunk {i}: {c['content'][:80]}...")
        if len(chunks) > 3:
            print(f"   ... and {len(chunks)-3} more")
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")


def cmd_generate(args):
    """Run a test generation with demo context."""
    print("🤖 Running test generation...")
    try:
        from services.generation.generator import ExamGenerator, ExamExporter

        # Mock pipeline with fake chunks (no DB/ChromaDB needed)
        from unittest.mock import MagicMock, patch

        mock_pipeline = MagicMock()
        mock_pipeline.retrieve_context.return_value = [
            "Machine learning is a branch of AI that learns from data.",
            "Supervised learning uses labeled data to train models.",
            "Neural networks are inspired by the human brain.",
        ]

        generator = ExamGenerator(ingestion_pipeline=mock_pipeline)
        questions = generator.generate_questions(
            material_ids=["demo"],
            question_type="multiple_choice",
            count=3,
            difficulty="medium",
            topic="machine learning",
        )

        exporter = ExamExporter()
        md = exporter.to_markdown("Demo Exam — Machine Learning", questions)
        print("\n" + "="*60)
        print(md)
        print("="*60)
        print(f"\n✅ Generated {len(questions)} questions")
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()


def cmd_reset_db(args):
    """Drop and recreate all tables. DEV ONLY."""
    confirm = input("⚠️  This will DROP ALL DATA. Type 'yes' to confirm: ")
    if confirm.strip().lower() != "yes":
        print("Aborted.")
        return
    from core.database import drop_tables, create_tables
    drop_tables()
    create_tables()
    print("✅ Database reset complete")


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="EduForge CLI — system management and diagnostics"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("setup",    help="Create DB tables and demo users")
    subparsers.add_parser("seed",     help="Insert demo material and run ingestion")
    subparsers.add_parser("status",   help="Check health of all services")
    subparsers.add_parser("generate", help="Run a test exam generation")
    subparsers.add_parser("reset-db", help="Drop and recreate all tables [DEV ONLY]")

    ingest_p = subparsers.add_parser("ingest", help="Manually ingest a file")
    ingest_p.add_argument("file", help="Path to file (PDF, DOCX, TXT, MD)")

    args = parser.parse_args()

    commands = {
        "setup":    cmd_setup,
        "seed":     cmd_seed,
        "status":   cmd_status,
        "ingest":   cmd_ingest,
        "generate": cmd_generate,
        "reset-db": cmd_reset_db,
    }

    fn = commands.get(args.command)
    if fn:
        fn(args)


if __name__ == "__main__":
    main()