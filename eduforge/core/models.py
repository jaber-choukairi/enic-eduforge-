"""
EduForge — SQLAlchemy ORM Models
All persistent entities: users, materials, exams, questions, jobs.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, JSON, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship
import enum


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.utcnow()


class Base(DeclarativeBase):
    pass


# ── Enums ─────────────────────────────────────────────────────────────────────

class MaterialStatus(str, enum.Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    READY      = "ready"
    FAILED     = "failed"


class JobStatus(str, enum.Enum):
    QUEUED     = "queued"
    RUNNING    = "running"
    COMPLETED  = "completed"
    FAILED     = "failed"


class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE      = "true_false"
    SHORT_ANSWER    = "short_answer"
    ESSAY           = "essay"
    FILL_BLANK      = "fill_blank"


class DifficultyLevel(str, enum.Enum):
    EASY   = "easy"
    MEDIUM = "medium"
    HARD   = "hard"


class UserRole(str, enum.Enum):
    STUDENT  = "student"
    TEACHER  = "teacher"
    ADMIN    = "admin"


# ── User ──────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id         = Column(String(36), primary_key=True, default=_uuid)
    email      = Column(String(255), unique=True, nullable=False, index=True)
    username   = Column(String(100), unique=True, nullable=False, index=True)
    hashed_pw  = Column(String(255), nullable=False)
    role       = Column(Enum(UserRole), default=UserRole.TEACHER, nullable=False)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    materials: Mapped[List["Material"]] = relationship("Material", back_populates="owner")
    exams:     Mapped[List["Exam"]]     = relationship("Exam",     back_populates="creator")


# ── Material ──────────────────────────────────────────────────────────────────

class Material(Base):
    __tablename__ = "materials"

    id           = Column(String(36), primary_key=True, default=_uuid)
    owner_id     = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title        = Column(String(500), nullable=False)
    description  = Column(Text, nullable=True)
    file_path    = Column(String(1000), nullable=True)
    file_type    = Column(String(20), nullable=True)
    file_size_kb = Column(Integer, nullable=True)
    subject      = Column(String(200), nullable=True, index=True)
    language     = Column(String(10), default="en")
    status       = Column(Enum(MaterialStatus), default=MaterialStatus.PENDING, nullable=False)
    chunk_count  = Column(Integer, default=0)
    vector_ids   = Column(JSON, default=list)      # ChromaDB doc IDs
    metadata_    = Column("metadata", JSON, default=dict)
    created_at   = Column(DateTime, default=_now, nullable=False)
    updated_at   = Column(DateTime, default=_now, onupdate=_now)

    owner: Mapped["User"]           = relationship("User", back_populates="materials")
    exams: Mapped[List["Exam"]]     = relationship("Exam", secondary="exam_materials", back_populates="materials")
    chunks: Mapped[List["Chunk"]]   = relationship("Chunk", back_populates="material")


# ── Chunk ─────────────────────────────────────────────────────────────────────

class Chunk(Base):
    __tablename__ = "chunks"

    id          = Column(String(36), primary_key=True, default=_uuid)
    material_id = Column(String(36), ForeignKey("materials.id"), nullable=False, index=True)
    content     = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    vector_id   = Column(String(100), nullable=True)   # ChromaDB ID
    token_count = Column(Integer, default=0)
    page_number = Column(Integer, nullable=True)
    metadata_   = Column("metadata", JSON, default=dict)
    created_at  = Column(DateTime, default=_now)

    material: Mapped["Material"] = relationship("Material", back_populates="chunks")


# ── Exam ──────────────────────────────────────────────────────────────────────

class ExamMaterial(Base):
    __tablename__ = "exam_materials"
    exam_id     = Column(String(36), ForeignKey("exams.id"),     primary_key=True)
    material_id = Column(String(36), ForeignKey("materials.id"), primary_key=True)


class Exam(Base):
    __tablename__ = "exams"

    id               = Column(String(36), primary_key=True, default=_uuid)
    creator_id       = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title            = Column(String(500), nullable=False)
    description      = Column(Text, nullable=True)
    subject          = Column(String(200), nullable=True)
    topic            = Column(String(500), nullable=True)
    difficulty       = Column(Enum(DifficultyLevel), default=DifficultyLevel.MEDIUM)
    num_questions    = Column(Integer, nullable=False)
    time_limit_min   = Column(Integer, nullable=True)
    instructions     = Column(Text, nullable=True)
    generation_cfg   = Column(JSON, default=dict)   # prompt params used
    model_version    = Column(String(100), nullable=True)
    is_published     = Column(Boolean, default=False)
    created_at       = Column(DateTime, default=_now, nullable=False)
    updated_at       = Column(DateTime, default=_now, onupdate=_now)

    creator:   Mapped["User"]              = relationship("User", back_populates="exams")
    materials: Mapped[List["Material"]]    = relationship("Material", secondary="exam_materials", back_populates="exams")
    questions: Mapped[List["Question"]]    = relationship("Question", back_populates="exam", cascade="all, delete-orphan")


# ── Question ──────────────────────────────────────────────────────────────────

class Question(Base):
    __tablename__ = "questions"

    id            = Column(String(36), primary_key=True, default=_uuid)
    exam_id       = Column(String(36), ForeignKey("exams.id"), nullable=False, index=True)
    question_type = Column(Enum(QuestionType), nullable=False)
    difficulty    = Column(Enum(DifficultyLevel), default=DifficultyLevel.MEDIUM)
    content       = Column(Text, nullable=False)          # The question text
    options       = Column(JSON, nullable=True)           # MCQ options list
    correct_answer = Column(Text, nullable=True)
    explanation   = Column(Text, nullable=True)
    rubric        = Column(Text, nullable=True)           # For essays
    points        = Column(Float, default=1.0)
    order_index   = Column(Integer, nullable=False, default=0)
    source_chunk_id = Column(String(36), ForeignKey("chunks.id"), nullable=True)
    raw_generation  = Column(Text, nullable=True)        # Raw LLM output
    created_at    = Column(DateTime, default=_now)

    exam: Mapped["Exam"] = relationship("Exam", back_populates="questions")


# ── TrainingJob ───────────────────────────────────────────────────────────────

class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id              = Column(String(36), primary_key=True, default=_uuid)
    created_by      = Column(String(36), ForeignKey("users.id"), nullable=False)
    status          = Column(Enum(JobStatus), default=JobStatus.QUEUED, nullable=False)
    model_name      = Column(String(200), nullable=False)
    base_model      = Column(String(200), nullable=False)
    material_ids    = Column(JSON, default=list)
    hyperparams     = Column(JSON, default=dict)
    mlflow_run_id   = Column(String(100), nullable=True)
    mlflow_run_url  = Column(String(500), nullable=True)
    model_artifact  = Column(String(1000), nullable=True)  # saved path
    metrics         = Column(JSON, default=dict)
    error_message   = Column(Text, nullable=True)
    started_at      = Column(DateTime, nullable=True)
    finished_at     = Column(DateTime, nullable=True)
    created_at      = Column(DateTime, default=_now)


# ── GenerationJob ─────────────────────────────────────────────────────────────

class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id            = Column(String(36), primary_key=True, default=_uuid)
    created_by    = Column(String(36), ForeignKey("users.id"), nullable=False)
    exam_id       = Column(String(36), ForeignKey("exams.id"), nullable=True)
    status        = Column(Enum(JobStatus), default=JobStatus.QUEUED, nullable=False)
    config        = Column(JSON, default=dict)
    celery_task_id = Column(String(200), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at    = Column(DateTime, nullable=True)
    finished_at   = Column(DateTime, nullable=True)
    created_at    = Column(DateTime, default=_now)
