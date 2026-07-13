"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("role", sa.String(50), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "repositories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("local_path", sa.String(1024), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("branch", sa.String(255), nullable=False, server_default="main"),
        sa.Column("total_files", sa.Integer, nullable=False, server_default="0"),
        sa.Column("indexed_files", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "repo_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("language", sa.String(50), nullable=True),
        sa.Column("size_bytes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_chunks", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_repo_files_repository_id", "repo_files", ["repository_id"])

    op.create_table(
        "code_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "file_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repo_files.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("start_line", sa.Integer, nullable=False, server_default="0"),
        sa.Column("end_line", sa.Integer, nullable=False, server_default="0"),
        # pgvector column — 384 dimensions for all-MiniLM-L6-v2
        sa.Column("embedding", sa.Text, nullable=True),  # overridden below
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    # Replace placeholder Text column with real vector type
    op.execute("ALTER TABLE code_chunks DROP COLUMN embedding")
    op.execute("ALTER TABLE code_chunks ADD COLUMN embedding vector(384)")
    op.create_index("ix_code_chunks_file_id", "code_chunks", ["file_id"])
    op.create_index("ix_code_chunks_repository_id", "code_chunks", ["repository_id"])
    # IVFFlat index for approximate nearest-neighbour search
    op.execute(
        "CREATE INDEX ix_code_chunks_embedding_ivfflat "
        "ON code_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    op.create_table(
        "review_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_path", sa.String(1024), nullable=True),
        sa.Column("review_type", sa.String(50), nullable=False, server_default="file"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("results", postgresql.JSON, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("llm_model", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_review_history_repository_id", "review_history", ["repository_id"])


def downgrade() -> None:
    op.drop_table("review_history")
    op.drop_table("code_chunks")
    op.drop_table("repo_files")
    op.drop_table("repositories")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
