import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base


class RepositoryStatus(str):
    pending = "pending"
    cloning = "cloning"
    indexing = "indexing"
    ready = "ready"
    error = "error"


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    local_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    branch: Mapped[str] = mapped_column(String(255), default="main", nullable=False)
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    indexed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    owner: Mapped["User"] = relationship("User", back_populates="repositories")  # noqa: F821
    files: Mapped[list["RepoFile"]] = relationship(  # noqa: F821
        "RepoFile", back_populates="repository", cascade="all, delete-orphan"
    )
    review_history: Mapped[list["ReviewHistory"]] = relationship(  # noqa: F821
        "ReviewHistory", back_populates="repository", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Repository id={self.id} name={self.name} status={self.status}>"
