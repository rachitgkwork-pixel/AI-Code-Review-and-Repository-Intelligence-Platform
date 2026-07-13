import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config import get_settings
from backend.database.connection import Base

settings = get_settings()


class RepoFile(Base):
    __tablename__ = "repo_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_chunks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    repository: Mapped["Repository"] = relationship(  # noqa: F821
        "Repository", back_populates="files"
    )
    chunks: Mapped[list["CodeChunk"]] = relationship(
        "CodeChunk", back_populates="file", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<RepoFile id={self.id} path={self.file_path}>"


class CodeChunk(Base):
    __tablename__ = "code_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repo_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # pgvector column — dimensionality matches EMBEDDING_DIMENSION in settings
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.embedding_dimension), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    file: Mapped[RepoFile] = relationship("RepoFile", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<CodeChunk id={self.id} file_id={self.file_id} index={self.chunk_index}>"
