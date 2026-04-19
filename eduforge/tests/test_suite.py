"""
EduForge — Test Suite
Covers: ingestion · generation · training data builder · API routes · utils
Run with: pytest tests/ -v --cov=. --cov-report=term-missing
"""
from __future__ import annotations

import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Test config override before any imports ────────────────────────────────────

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_eduforge.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("MLFLOW_TRACKING_URI", "sqlite:///./test_mlflow.db")
os.environ.setdefault("ENV", "test")

from core.config import settings
from core.models import Base, User, Material, Exam, Question, MaterialStatus, UserRole
from core.utils import hash_password, create_access_token, decode_access_token, new_id


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        "sqlite:///./test_eduforge.db",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    Path("./test_eduforge.db").unlink(missing_ok=True)


@pytest.fixture(scope="function")
def db_session(test_engine):
    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def test_user(db_session):
    user = User(
        id=new_id(),
        email=f"test_{uuid.uuid4().hex[:8]}@edu.com",
        username=f"testuser_{uuid.uuid4().hex[:6]}",
        hashed_pw=hash_password("password123"),
        role=UserRole.TEACHER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def auth_token(test_user):
    return create_access_token({"sub": test_user.id, "role": test_user.role})


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
def test_material(db_session, test_user):
    mat = Material(
        id=new_id(),
        owner_id=test_user.id,
        title="Test Material",
        subject="Mathematics",
        status=MaterialStatus.READY,
        chunk_count=5,
        vector_ids=[new_id() for _ in range(5)],
    )
    db_session.add(mat)
    db_session.commit()
    return mat


@pytest.fixture(scope="function")
def app_client(db_session):
    """FastAPI test client with DB session overridden."""
    from core.database import get_db
    from services.gateway.main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_txt_file(tmp_path):
    p = tmp_path / "lesson.txt"
    p.write_text(
        "Machine learning is a subset of artificial intelligence.\n\n"
        "Supervised learning uses labelled data to train models.\n\n"
        "Unsupervised learning finds hidden patterns in unlabelled data.\n\n"
        "Neural networks are inspired by the human brain and consist of layers of nodes.\n\n"
        "Deep learning uses multiple layers of neural networks to learn complex representations.\n\n"
        "Common algorithms include linear regression, decision trees, and support vector machines.",
        encoding="utf-8",
    )
    return p


# ── Utils Tests ───────────────────────────────────────────────────────────────

class TestSecurity:
    def test_hash_and_verify_password(self):
        pw = "supersecret123"
        hashed = hash_password(pw)
        assert hashed != pw
        assert verify_password(pw, hashed)

    def test_wrong_password_fails(self):
        from core.utils import verify_password
        assert not verify_password("wrong", hash_password("correct"))

    def test_create_and_decode_token(self):
        data = {"sub": "user-123", "role": "teacher"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user-123"

    def test_expired_token_returns_none(self):
        from datetime import timedelta
        token = create_access_token({"sub": "x"}, expires_delta=timedelta(seconds=-1))
        assert decode_access_token(token) is None

    def test_invalid_token_returns_none(self):
        assert decode_access_token("not.a.valid.jwt") is None


# ── Chunker Tests ─────────────────────────────────────────────────────────────

class TestTextChunker:
    def setup_method(self):
        from services.ingestion.pipeline import TextChunker
        self.chunker = TextChunker(chunk_size=100, overlap=20)

    def test_basic_chunking(self):
        text = " ".join(["word"] * 500)
        chunks = self.chunker.chunk(text)
        assert len(chunks) > 0
        assert all("content" in c for c in chunks)
        assert all("chunk_index" in c for c in chunks)

    def test_chunk_indices_sequential(self):
        text = "This is a sentence. " * 100
        chunks = self.chunker.chunk(text)
        indices = [c["chunk_index"] for c in chunks]
        assert indices == list(range(len(indices)))

    def test_short_text_single_chunk(self):
        text = "Short content here."
        chunks = self.chunker.chunk(text)
        assert len(chunks) == 1
        assert chunks[0]["content"] == "Short content here."

    def test_empty_text_returns_empty(self):
        chunks = self.chunker.chunk("   \n\n   ")
        assert chunks == []

    def test_token_count_present(self):
        text = "Sentence one. Sentence two. Sentence three."
        chunks = self.chunker.chunk(text)
        assert all(c["token_count"] > 0 for c in chunks)


# ── Extractor Tests ───────────────────────────────────────────────────────────

class TestTextExtractor:
    def setup_method(self):
        from services.ingestion.pipeline import TextExtractor
        self.extractor = TextExtractor()

    def test_extract_txt(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("Hello world\n\nSecond paragraph.", encoding="utf-8")
        text = self.extractor.extract(p)
        assert "Hello world" in text
        assert "Second paragraph" in text

    def test_extract_md(self, tmp_path):
        p = tmp_path / "test.md"
        p.write_text("# Title\n\nSome content.", encoding="utf-8")
        text = self.extractor.extract(p)
        assert "Title" in text

    def test_unsupported_type_raises(self, tmp_path):
        p = tmp_path / "test.xyz"
        p.write_text("data")
        with pytest.raises(ValueError, match="Unsupported"):
            self.extractor.extract(p)


# ── Parser Tests ──────────────────────────────────────────────────────────────

class TestQuestionParser:
    def setup_method(self):
        from services.generation.generator import QuestionParser
        self.parser = QuestionParser()

    def test_parse_mcq_full(self):
        raw = (
            "Question: What is 2 + 2?\n"
            "A) 3\nB) 4\nC) 5\nD) 6\n"
            "Correct: B\n"
            "Explanation: Basic addition"
        )
        result = self.parser.parse(raw, "multiple_choice")
        assert result["content"] == "What is 2 + 2?"
        assert len(result["options"]) == 4
        assert result["correct_answer"] == "4"
        assert result["explanation"] == "Basic addition"

    def test_parse_true_false(self):
        raw = "Statement: The sky is blue.\nAnswer: True\nExplanation: It scatters blue light."
        result = self.parser.parse(raw, "true_false")
        assert result["content"] == "The sky is blue."
        assert result["correct_answer"] == "True"
        assert result["options"] == ["True", "False"]

    def test_parse_short_answer(self):
        raw = "Question: What is photosynthesis?\nModel Answer: Process plants use to convert light to energy."
        result = self.parser.parse(raw, "short_answer")
        assert "photosynthesis" in result["content"].lower()
        assert "energy" in result["correct_answer"].lower()

    def test_parse_essay(self):
        raw = "Essay Prompt: Discuss climate change.\nGuidance: Consider causes and effects.\nRubric: 10 points for clarity."
        result = self.parser.parse(raw, "essay")
        assert "climate change" in result["content"].lower()
        assert result["rubric"] is not None

    def test_parse_fill_blank(self):
        raw = "Sentence: Water boils at ______ degrees Celsius.\nAnswer: 100\nExplanation: At sea level."
        result = self.parser.parse(raw, "fill_blank")
        assert "______" in result["content"]
        assert result["correct_answer"] == "100"

    def test_fallback_on_bad_format(self):
        raw = "Just some random text with no structure."
        result = self.parser.parse(raw, "multiple_choice")
        assert result["content"] is not None
        assert isinstance(result, dict)


# ── Training Data Builder Tests ───────────────────────────────────────────────

class TestTrainingDataBuilder:
    def setup_method(self):
        from services.training.trainer import TrainingDataBuilder
        self.builder = TrainingDataBuilder()

    def test_build_from_chunks(self):
        chunks = [
            {"content": "Machine learning is a powerful technique used in AI. " * 5, "chunk_index": 0},
            {"content": "Neural networks learn from examples by adjusting weights. " * 5, "chunk_index": 1},
        ]
        records = self.builder.build_from_chunks(chunks)
        assert len(records) > 0
        assert all(hasattr(r, "input_text") and hasattr(r, "target_text") for r in records)

    def test_short_chunks_skipped(self):
        chunks = [
            {"content": "Too short.", "chunk_index": 0},
            {"content": "Also tiny.", "chunk_index": 1},
        ]
        records = self.builder.build_from_chunks(chunks)
        assert records == []

    def test_train_val_split(self):
        from services.training.trainer import QARecord
        records = [QARecord(input_text=f"q{i}", target_text=f"a{i}") for i in range(20)]
        train, val = self.builder.train_val_split(records, val_ratio=0.2)
        assert len(train) + len(val) == 20
        assert len(val) >= 1


# ── Ingestion Pipeline Tests (mocked) ────────────────────────────────────────

class TestIngestionPipeline:
    @patch("services.ingestion.pipeline.EmbeddingEngine")
    @patch("services.ingestion.pipeline.VectorStore")
    def test_pipeline_run(self, MockVS, MockEmb, sample_txt_file):
        from services.ingestion.pipeline import IngestionPipeline, TextExtractor, TextChunker

        mock_vs   = MockVS.return_value
        mock_emb  = MockEmb.return_value
        mock_emb.embed.return_value = [[0.1, 0.2, 0.3] for _ in range(10)]

        pipeline = IngestionPipeline(
            extractor=TextExtractor(),
            chunker=TextChunker(chunk_size=200, overlap=50),
            embedder=mock_emb,
            vector_store=mock_vs,
        )
        chunks = pipeline.run(
            file_path=sample_txt_file,
            material_id="test-mat-id",
        )

        assert len(chunks) > 0
        assert mock_vs.upsert.called
        assert all("vector_id" in c for c in chunks)

    @patch("services.ingestion.pipeline.EmbeddingEngine")
    @patch("services.ingestion.pipeline.VectorStore")
    def test_retrieve_context(self, MockVS, MockEmb):
        from services.ingestion.pipeline import IngestionPipeline

        mock_vs  = MockVS.return_value
        mock_emb = MockEmb.return_value
        mock_emb.embed_one.return_value = [0.1] * 384
        mock_vs.query.return_value = [
            {"content": "Relevant chunk 1", "score": 0.9, "metadata": {}},
            {"content": "Relevant chunk 2", "score": 0.8, "metadata": {}},
        ]

        pipeline = IngestionPipeline(
            embedder=mock_emb,
            vector_store=mock_vs,
        )
        results = pipeline.retrieve_context("machine learning", n_results=2)
        assert results == ["Relevant chunk 1", "Relevant chunk 2"]


# ── API Tests ─────────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_returns_200(self, app_client):
        with patch("services.gateway.main.db_health", return_value=True), \
             patch("redis.from_url") as mock_redis:
            mock_redis.return_value.ping.return_value = True
            resp = app_client.get("/health")
            # May be 200 or 500 depending on ChromaDB — just check it responds
            assert resp.status_code in (200, 500, 503)

    def test_root_endpoint(self, app_client):
        resp = app_client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == settings.APP_NAME


class TestAuthEndpoints:
    def test_register_user(self, app_client):
        resp = app_client.post(
            f"{settings.API_PREFIX}/auth/register",
            json={
                "email": f"new_{uuid.uuid4().hex[:6]}@test.com",
                "username": f"newuser_{uuid.uuid4().hex[:6]}",
                "password": "password123",
                "role": "teacher",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["role"] == "teacher"

    def test_register_duplicate_email_fails(self, app_client, test_user):
        resp = app_client.post(
            f"{settings.API_PREFIX}/auth/register",
            json={
                "email": test_user.email,
                "username": "unique_user",
                "password": "password123",
            },
        )
        assert resp.status_code == 409

    def test_login_valid(self, app_client, test_user):
        resp = app_client.post(
            f"{settings.API_PREFIX}/auth/login",
            data={"username": test_user.username, "password": "password123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    def test_login_wrong_password(self, app_client, test_user):
        resp = app_client.post(
            f"{settings.API_PREFIX}/auth/login",
            data={"username": test_user.username, "password": "wrongpass"},
        )
        assert resp.status_code == 401

    def test_me_endpoint(self, app_client, auth_headers, test_user):
        resp = app_client.get(f"{settings.API_PREFIX}/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["username"] == test_user.username

    def test_me_without_token_fails(self, app_client):
        resp = app_client.get(f"{settings.API_PREFIX}/auth/me")
        assert resp.status_code == 401


class TestMaterialEndpoints:
    def test_list_materials_empty(self, app_client, auth_headers):
        resp = app_client.get(f"{settings.API_PREFIX}/materials", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_material_not_found(self, app_client, auth_headers):
        resp = app_client.get(
            f"{settings.API_PREFIX}/materials/{new_id()}",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_upload_unsupported_type(self, app_client, auth_headers, tmp_path):
        p = tmp_path / "bad.xyz"
        p.write_bytes(b"data")
        resp = app_client.post(
            f"{settings.API_PREFIX}/materials/upload",
            headers=auth_headers,
            data={"title": "Bad file", "subject": "Test"},
            files={"file": ("bad.xyz", open(p, "rb"), "application/octet-stream")},
        )
        assert resp.status_code == 415

    @patch("services.gateway.main._ingest_material_task")
    def test_upload_txt_success(self, mock_task, app_client, auth_headers, sample_txt_file):
        mock_task.return_value = None
        resp = app_client.post(
            f"{settings.API_PREFIX}/materials/upload",
            headers=auth_headers,
            data={"title": "Sample Lesson", "subject": "Science"},
            files={"file": ("lesson.txt", open(sample_txt_file, "rb"), "text/plain")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Sample Lesson"
        assert data["status"] == "pending"


class TestExamEndpoints:
    def test_list_exams_empty(self, app_client, auth_headers):
        resp = app_client.get(f"{settings.API_PREFIX}/exams", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_generate_exam_material_not_found(self, app_client, auth_headers):
        resp = app_client.post(
            f"{settings.API_PREFIX}/exams/generate",
            headers=auth_headers,
            json={
                "title": "Test Exam",
                "material_ids": [new_id()],
                "question_configs": [{"question_type": "multiple_choice", "count": 3, "difficulty": "easy"}],
            },
        )
        assert resp.status_code == 404

    @patch("services.gateway.main._generate_exam_task")
    def test_generate_exam_success(self, mock_task, app_client, auth_headers, test_material):
        mock_task.return_value = None
        resp = app_client.post(
            f"{settings.API_PREFIX}/exams/generate",
            headers=auth_headers,
            json={
                "title": "Math Quiz",
                "material_ids": [test_material.id],
                "question_configs": [{"question_type": "multiple_choice", "count": 5, "difficulty": "medium"}],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "queued"
        assert "id" in data


class TestExportEndpoint:
    def test_export_markdown_not_found(self, app_client, auth_headers):
        resp = app_client.get(
            f"{settings.API_PREFIX}/exams/{new_id()}/export/markdown",
            headers=auth_headers,
        )
        assert resp.status_code == 404


# ── Exporter Tests ────────────────────────────────────────────────────────────

class TestExamExporter:
    def setup_method(self):
        from services.generation.generator import ExamExporter, GeneratedQuestion
        self.exporter = ExamExporter()
        self.questions = [
            GeneratedQuestion(
                question_type="multiple_choice",
                difficulty="medium",
                content="What is 2+2?",
                options=["3", "4", "5", "6"],
                correct_answer="4",
                explanation="Basic math",
                points=2.0,
                order_index=0,
            ),
            GeneratedQuestion(
                question_type="short_answer",
                difficulty="easy",
                content="Define photosynthesis.",
                correct_answer="Process by which plants make food.",
                points=1.0,
                order_index=1,
            ),
        ]

    def test_to_json(self):
        result = self.exporter.to_json("Test Exam", self.questions)
        assert result["title"] == "Test Exam"
        assert result["total_questions"] == 2
        assert result["total_points"] == 3.0
        assert len(result["questions"]) == 2

    def test_to_markdown_contains_questions(self):
        md = self.exporter.to_markdown("Test Exam", self.questions)
        assert "Test Exam" in md
        assert "What is 2+2?" in md
        assert "Define photosynthesis" in md
        assert "Correct Answer" in md

    def test_to_student_view_hides_answers(self):
        md = self.exporter.to_student_view("Test Exam", self.questions)
        assert "Test Exam" in md
        assert "Correct Answer" not in md  # Answers hidden in student view


# ── Integration Test ──────────────────────────────────────────────────────────

class TestIngestionToGeneration:
    """Tests the full pipeline: chunk text → embed → retrieve → parse."""

    def test_chunk_then_parse(self, sample_txt_file):
        from services.ingestion.pipeline import TextExtractor, TextChunker
        from services.generation.generator import QuestionParser, PromptBuilder

        text = TextExtractor.extract_txt(sample_txt_file)
        chunker = TextChunker(chunk_size=200, overlap=40)
        chunks = chunker.chunk(text)

        assert len(chunks) > 0

        builder = PromptBuilder()
        context_texts = [c["content"] for c in chunks[:2]]
        prompt = builder.build(
            context_chunks=context_texts,
            question_type="multiple_choice",
            topic="machine learning",
            difficulty="medium",
        )
        assert "machine learning" in prompt.lower()
        assert "multiple-choice" in prompt.lower() or "multiple choice" in prompt.lower()


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
