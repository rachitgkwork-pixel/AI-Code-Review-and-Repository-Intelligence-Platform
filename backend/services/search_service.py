"""Semantic search over indexed code chunks using pgvector cosine similarity."""

import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.code_chunk import CodeChunk, RepoFile
from backend.schemas.search import SearchResult
from backend.services.embedding_service import EmbeddingService
from backend.utils.cache import CacheBackend
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class SearchService:
    def __init__(
        self,
        db: AsyncSession,
        embedding_svc: EmbeddingService,
        cache: CacheBackend,
    ) -> None:
        self.db = db
        self.embedding_svc = embedding_svc
        self.cache = cache

    async def search(
        self,
        query: str,
        top_k: int = 5,
        repository_id: uuid.UUID | None = None,
    ) -> list[SearchResult]:
        cache_key = f"search:{query}:{repository_id}:{top_k}"
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug("Cache hit for query '%s'", query)
            return [SearchResult(**r) for r in cached]

        query_vector = self.embedding_svc.encode_one(query)

        # pgvector cosine distance operator: <=> (lower = more similar)
        # We join with repo_files to get the file path
        vector_literal = f"[{','.join(map(str, query_vector))}]"

        filters = ""
        if repository_id:
            filters = f"AND c.repository_id = '{repository_id}'"

        raw_sql = text(f"""
            SELECT
                c.id            AS chunk_id,
                c.repository_id,
                c.content,
                c.start_line,
                c.end_line,
                f.file_path,
                1 - (c.embedding <=> '{vector_literal}'::vector) AS similarity
            FROM code_chunks c
            JOIN repo_files f ON f.id = c.file_id
            WHERE c.embedding IS NOT NULL
            {filters}
            ORDER BY c.embedding <=> '{vector_literal}'::vector
            LIMIT :top_k
        """)

        result = await self.db.execute(raw_sql, {"top_k": top_k})
        rows = result.mappings().all()

        search_results = [
            SearchResult(
                chunk_id=row["chunk_id"],
                file_path=row["file_path"],
                repository_id=row["repository_id"],
                content=row["content"],
                similarity=float(row["similarity"]),
                start_line=row["start_line"],
                end_line=row["end_line"],
            )
            for row in rows
        ]

        await self.cache.set(cache_key, [r.model_dump(mode="json") for r in search_results], ttl=120)
        return search_results
