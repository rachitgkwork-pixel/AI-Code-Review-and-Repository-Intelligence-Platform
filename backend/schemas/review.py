import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class ReviewIssue(BaseModel):
    issue: str
    severity: Severity
    description: str
    suggested_fix: str
    line_range: str | None = None  # e.g. "42-55"


class FileReviewRequest(BaseModel):
    repository_id: uuid.UUID
    file_path: str


class RepositoryReviewRequest(BaseModel):
    repository_id: uuid.UUID


class ReviewResponse(BaseModel):
    review_id: uuid.UUID
    repository_id: uuid.UUID
    file_path: str | None
    review_type: str
    status: str
    issues: list[ReviewIssue]
    llm_model: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
