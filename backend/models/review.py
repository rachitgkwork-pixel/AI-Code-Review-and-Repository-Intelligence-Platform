import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base


class ReviewHistory(Base):
    __tablename__ = "review_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Optional: scoped to a specific file, or None for full-repo review
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    review_type: Mapped[str] = mapped_column(
        String(50), default="file", nullable=False
    )  # "file" | "repository"
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # "pending" | "completed" | "error"
    # Structured list of ReviewIssue objects stored as JSON
    results: Mapped[list | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    repository: Mapped["Repository"] = relationship(  # noqa: F821
        "Repository", back_populates="review_history"
    )
    requested_by: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="review_history"
    )

    def __repr__(self) -> str:
        return f"<ReviewHistory id={self.id} status={self.status}>"
