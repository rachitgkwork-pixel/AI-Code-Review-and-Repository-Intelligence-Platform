import uuid
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1024)
    repository_id: uuid.UUID | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    chunk_id: uuid.UUID
    file_path: str
    repository_id: uuid.UUID
    content: str
    similarity: float
    start_line: int
    end_line: int


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int
