"""FastAPI dependency factories shared across route modules."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.connection import get_db
from backend.services.embedding_service import EmbeddingService, get_embedding_service
from backend.services.indexing_service import IndexingService
from backend.services.repository_service import RepositoryService
from backend.services.review_service import ReviewService
from backend.services.search_service import SearchService
from backend.utils.cache import CacheBackend, get_cache


def get_repo_service(db: AsyncSession = Depends(get_db)) -> RepositoryService:
    return RepositoryService(db)


def get_indexing_service(
    db: AsyncSession = Depends(get_db),
    embedding_svc: EmbeddingService = Depends(get_embedding_service),
) -> IndexingService:
    return IndexingService(db, embedding_svc)


def get_search_service(
    db: AsyncSession = Depends(get_db),
    embedding_svc: EmbeddingService = Depends(get_embedding_service),
    cache: CacheBackend = Depends(get_cache),
) -> SearchService:
    return SearchService(db, embedding_svc, cache)


def get_review_service(db: AsyncSession = Depends(get_db)) -> ReviewService:
    return ReviewService(db)
