"""
EduForge — Core Utilities: Logging · Security · Shared Pydantic Schemas
Compatible with Pydantic v2.
"""
from __future__ import annotations

import hashlib
import logging
import sys
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import jwt
from passlib.context import CryptContext
from pythonjsonlogger import jsonlogger
from pydantic import BaseModel, EmailStr, Field, field_validator

from core.config import settings


# ── Logging ──────────────────────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stdout)
    fmt = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    logger.propagate = False
    return logger


logger = get_logger("eduforge.core")


# ── Security ─────────────────────────────────────────────────────────────────

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
    )
    payload.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("JWT expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("JWT invalid: %s", e)
        return None


def generate_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


# ── Shared Pydantic Schemas ───────────────────────────────────────────────────

class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[Any]


class HealthResponse(BaseModel):
    status: str
    version: str
    database: bool
    redis: bool
    vector_db: bool
    timestamp: datetime


# ── User Schemas ──────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    role: str = "teacher"

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.replace("_", "").isalnum():
            raise ValueError("Username must be alphanumeric")
        return v.lower()


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = settings.JWT_EXPIRY_MINUTES * 60


# ── Material Schemas ──────────────────────────────────────────────────────────

class MaterialCreate(BaseModel):
    title: str = Field(max_length=500)
    description: Optional[str] = None
    subject: Optional[str] = None
    language: str = "en"


class MaterialOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    description: Optional[str] = None
    subject: Optional[str] = None
    file_type: Optional[str] = None
    file_size_kb: Optional[int] = None
    status: str
    chunk_count: int
    created_at: datetime


# ── Exam Schemas ──────────────────────────────────────────────────────────────

class QuestionConfig(BaseModel):
    question_type: str = "multiple_choice"
    count: int = Field(default=5, ge=1, le=20)
    difficulty: str = "medium"


class ExamGenerateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    material_ids: List[str] = Field(min_length=1)
    topic: Optional[str] = None
    question_configs: List[QuestionConfig] = Field(
        default_factory=lambda: [QuestionConfig()]
    )
    time_limit_min: Optional[int] = None
    instructions: Optional[str] = None

    @field_validator("question_configs")
    @classmethod
    def validate_total(cls, v):
        total = sum(qc.count for qc in v)
        if total > 50:
            raise ValueError("Total questions cannot exceed 50")
        return v


class QuestionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    question_type: str
    difficulty: str
    content: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    rubric: Optional[str] = None
    points: float
    order_index: int


class ExamOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    description: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None
    difficulty: str
    num_questions: int
    time_limit_min: Optional[int] = None
    instructions: Optional[str] = None
    is_published: bool
    questions: List[QuestionOut] = []
    created_at: datetime


# ── Training Schemas ──────────────────────────────────────────────────────────

class TrainingRequest(BaseModel):
    model_name: str
    material_ids: List[str] = Field(min_length=1)
    base_model: str = settings.GENERATION_MODEL
    hyperparams: Dict[str, Any] = Field(default_factory=dict)


class TrainingJobOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    status: str
    model_name: str
    base_model: str
    mlflow_run_id: Optional[str] = None
    metrics: Dict[str, Any]
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime


# ── Generation Job Schemas ────────────────────────────────────────────────────

class GenerationJobOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    exam_id: Optional[str] = None
    status: str
    celery_task_id: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime


# ── Helpers ───────────────────────────────────────────────────────────────────

def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.utcnow()