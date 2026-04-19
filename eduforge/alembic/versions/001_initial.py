"""Initial schema — all EduForge tables

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-01 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("hashed_pw", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="teacher"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])

    # ── materials ─────────────────────────────────────────────────────────────
    op.create_table(
        "materials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("file_type", sa.String(20), nullable=True),
        sa.Column("file_size_kb", sa.Integer(), nullable=True),
        sa.Column("subject", sa.String(200), nullable=True),
        sa.Column("language", sa.String(10), server_default="en"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("chunk_count", sa.Integer(), server_default="0"),
        sa.Column("vector_ids", sa.JSON(), server_default="[]"),
        sa.Column("metadata", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_materials_owner_id", "materials", ["owner_id"])
    op.create_index("ix_materials_subject", "materials", ["subject"])

    # ── chunks ────────────────────────────────────────────────────────────────
    op.create_table(
        "chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("material_id", sa.String(36), sa.ForeignKey("materials.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("vector_id", sa.String(100), nullable=True),
        sa.Column("token_count", sa.Integer(), server_default="0"),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_chunks_material_id", "chunks", ["material_id"])

    # ── exams ─────────────────────────────────────────────────────────────────
    op.create_table(
        "exams",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("creator_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("subject", sa.String(200), nullable=True),
        sa.Column("topic", sa.String(500), nullable=True),
        sa.Column("difficulty", sa.String(20), server_default="medium"),
        sa.Column("num_questions", sa.Integer(), nullable=False),
        sa.Column("time_limit_min", sa.Integer(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("generation_cfg", sa.JSON(), server_default="{}"),
        sa.Column("model_version", sa.String(100), nullable=True),
        sa.Column("is_published", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_exams_creator_id", "exams", ["creator_id"])

    # ── exam_materials (junction) ──────────────────────────────────────────────
    op.create_table(
        "exam_materials",
        sa.Column("exam_id", sa.String(36), sa.ForeignKey("exams.id"), primary_key=True),
        sa.Column("material_id", sa.String(36), sa.ForeignKey("materials.id"), primary_key=True),
    )

    # ── questions ─────────────────────────────────────────────────────────────
    op.create_table(
        "questions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("exam_id", sa.String(36), sa.ForeignKey("exams.id"), nullable=False),
        sa.Column("question_type", sa.String(30), nullable=False),
        sa.Column("difficulty", sa.String(20), server_default="medium"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("correct_answer", sa.Text(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("rubric", sa.Text(), nullable=True),
        sa.Column("points", sa.Float(), server_default="1.0"),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_chunk_id", sa.String(36), nullable=True),
        sa.Column("raw_generation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_questions_exam_id", "questions", ["exam_id"])

    # ── training_jobs ─────────────────────────────────────────────────────────
    op.create_table(
        "training_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("model_name", sa.String(200), nullable=False),
        sa.Column("base_model", sa.String(200), nullable=False),
        sa.Column("material_ids", sa.JSON(), server_default="[]"),
        sa.Column("hyperparams", sa.JSON(), server_default="{}"),
        sa.Column("mlflow_run_id", sa.String(100), nullable=True),
        sa.Column("mlflow_run_url", sa.String(500), nullable=True),
        sa.Column("model_artifact", sa.String(1000), nullable=True),
        sa.Column("metrics", sa.JSON(), server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )

    # ── generation_jobs ────────────────────────────────────────────────────────
    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("exam_id", sa.String(36), sa.ForeignKey("exams.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("config", sa.JSON(), server_default="{}"),
        sa.Column("celery_task_id", sa.String(200), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )


def downgrade() -> None:
    op.drop_table("generation_jobs")
    op.drop_table("training_jobs")
    op.drop_table("questions")
    op.drop_table("exam_materials")
    op.drop_table("exams")
    op.drop_table("chunks")
    op.drop_table("materials")
    op.drop_table("users")
