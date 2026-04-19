"""
EduForge — Core Configuration
Compatible with Pydantic v2 + pydantic-settings.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "EduForge"
    APP_VERSION: str = "1.0.0"
    ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-please"

    # ── API ──────────────────────────────────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8501",
        "http://localhost:8502",
    ]

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://eduforge:eduforge@127.0.0.1:5432/eduforge"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # ── Redis ────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── ChromaDB ─────────────────────────────────────────────────────────────
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8100
    CHROMA_COLLECTION_NAME: str = "edu_materials"

    # ── MLflow ───────────────────────────────────────────────────────────────
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_NAME: str = "eduforge-training"
    MODEL_REGISTRY_NAME: str = "eduforge-exam-generator"

    # ── Model ────────────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    GENERATION_MODEL: str = "google/flan-t5-small"
    MODEL_CACHE_DIR: Path = BASE_DIR / "data" / "models"
    MAX_INPUT_TOKENS: int = 512
    MAX_OUTPUT_TOKENS: int = 256
    GENERATION_TEMPERATURE: float = 0.7
    GENERATION_TOP_P: float = 0.9

    # ── Ingestion ────────────────────────────────────────────────────────────
    UPLOAD_DIR: Path = BASE_DIR / "data" / "raw"
    PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    MAX_FILE_SIZE_MB: int = 50
    SUPPORTED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".md"]

    # ── Training ─────────────────────────────────────────────────────────────
    TRAIN_BATCH_SIZE: int = 4
    EVAL_BATCH_SIZE: int = 8
    NUM_TRAIN_EPOCHS: int = 3
    LEARNING_RATE: float = 5e-5
    WARMUP_STEPS: int = 100
    SAVE_STEPS: int = 500
    EVAL_STEPS: int = 500
    FP16: bool = False
    GRADIENT_ACCUMULATION_STEPS: int = 4

    # ── Generation ───────────────────────────────────────────────────────────
    DEFAULT_EXAM_QUESTIONS: int = 10
    MAX_EXAM_QUESTIONS: int = 50
    SUPPORTED_QUESTION_TYPES: List[str] = [
        "multiple_choice", "true_false", "short_answer", "essay", "fill_blank",
    ]
    SUPPORTED_DIFFICULTY_LEVELS: List[str] = ["easy", "medium", "hard"]

    # ── Auth ─────────────────────────────────────────────────────────────────
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60
    RATE_LIMIT_PER_MINUTE: int = 60

    # ── Logging ──────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    @field_validator("MODEL_CACHE_DIR", "UPLOAD_DIR", "PROCESSED_DIR", mode="before")
    @classmethod
    def create_dirs(cls, v):
        Path(v).mkdir(parents=True, exist_ok=True)
        return Path(v)


settings = Settings()


PROMPT_TEMPLATES = {
    "multiple_choice": (
        "Based on the following educational material, generate a multiple-choice question.\n\n"
        "Material:\n{context}\n\nTopic: {topic}\nDifficulty: {difficulty}\n\n"
        "Generate a question with 4 options (A, B, C, D) and mark the correct answer.\n"
        "Format:\nQuestion: ...\nA) ...\nB) ...\nC) ...\nD) ...\nCorrect: [letter]\nExplanation: ..."
    ),
    "true_false": (
        "Based on the following educational material, generate a true/false question.\n\n"
        "Material:\n{context}\n\nTopic: {topic}\nDifficulty: {difficulty}\n\n"
        "Format:\nStatement: ...\nAnswer: [True/False]\nExplanation: ..."
    ),
    "short_answer": (
        "Based on the following educational material, generate a short-answer question.\n\n"
        "Material:\n{context}\n\nTopic: {topic}\nDifficulty: {difficulty}\n\n"
        "Format:\nQuestion: ...\nModel Answer: ...\nKey Points: ..."
    ),
    "essay": (
        "Based on the following educational material, generate an essay question.\n\n"
        "Material:\n{context}\n\nTopic: {topic}\nDifficulty: {difficulty}\n\n"
        "Format:\nEssay Prompt: ...\nGuidance: ...\nRubric: ..."
    ),
    "fill_blank": (
        "Based on the following educational material, generate a fill-in-the-blank question.\n\n"
        "Material:\n{context}\n\nTopic: {topic}\nDifficulty: {difficulty}\n\n"
        "Format:\nSentence: ... ______ ...\nAnswer: ...\nExplanation: ..."
    ),
}