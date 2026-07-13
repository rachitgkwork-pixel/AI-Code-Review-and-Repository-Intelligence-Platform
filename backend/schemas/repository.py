import uuid
from datetime import datetime

from pydantic import BaseModel, HttpUrl


class RepositoryCreate(BaseModel):
    name: str
    url: str
    description: str | None = None
    branch: str = "main"


class RepositoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    url: str
    description: str | None
    status: str
    branch: str
    total_files: int
    indexed_files: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RepositoryStatusResponse(BaseModel):
    id: uuid.UUID
    status: str
    total_files: int
    indexed_files: int
    error_message: str | None

    model_config = {"from_attributes": True}
