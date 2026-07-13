"""Indexing service: clones a repo, reads source files, chunks them, generates
embeddings, and persists everything to PostgreSQL via pgvector.
"""

import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.models.code_chunk import CodeChunk, RepoFile
from backend.models.repository import Repository
from backend.services.embedding_service import EmbeddingService
from backend.services.repository_service import RepositoryService
from backend.utils.file_utils import chunk_text, detect_language, iter_source_files
from backend.utils.git_utils import clone_repository
from backend.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class IndexingService:
    def __init__(self, db: AsyncSession, embedding_svc: EmbeddingService) -> None:
        self.db = db
        self.embedding_svc = embedding_svc
        self.repo_svc = RepositoryService(db)

    async def index_repository(self, repo: Repository) -> None:
        """Full indexing pipeline for *repo*. Updates status throughout."""
        try:
            await self.repo_svc.update_status(repo.id, "cloning")

            dest = Path(settings.repos_base_dir) / str(repo.id)
            clone_repository(repo.url, dest, repo.branch)

            await self.repo_svc.update_status(repo.id, "indexing", local_path=str(dest))

            source_files = list(iter_source_files(dest))
            await self.repo_svc.update_status(repo.id, "indexing", total_files=len(source_files))

            indexed = 0
            for file_path in source_files:
                try:
                    await self._index_file(repo.id, file_path, dest)
                    indexed += 1
                    if indexed % 10 == 0:
                        await self.repo_svc.update_status(repo.id, "indexing", indexed_files=indexed)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Skipping %s: %s", file_path, exc)

            await self.repo_svc.update_status(
                repo.id, "ready", indexed_files=indexed
            )
            logger.info("Indexing complete for repo %s (%d files)", repo.id, indexed)

        except Exception as exc:
            logger.exception("Indexing failed for repo %s", repo.id)
            await self.repo_svc.update_status(repo.id, "error", error_message=str(exc))

    async def _index_file(
        self, repo_id: uuid.UUID, file_path: Path, repo_root: Path
    ) -> None:
        relative_path = str(file_path.relative_to(repo_root))
        max_bytes = settings.max_file_size_kb * 1024

        if file_path.stat().st_size > max_bytes:
            logger.debug("Skipping large file %s", relative_path)
            return

        text = file_path.read_text(encoding="utf-8", errors="replace")
        language = detect_language(file_path)

        repo_file = RepoFile(
            repository_id=repo_id,
            file_path=relative_path,
            language=language,
            size_bytes=file_path.stat().st_size,
        )
        self.db.add(repo_file)
        await self.db.flush()  # get repo_file.id

        raw_chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        texts = [c[0] for c in raw_chunks]
        embeddings = self.embedding_svc.encode(texts)

        for idx, ((content, start, end), vector) in enumerate(zip(raw_chunks, embeddings)):
            chunk = CodeChunk(
                file_id=repo_file.id,
                repository_id=repo_id,
                content=content,
                chunk_index=idx,
                start_line=start,
                end_line=end,
                embedding=vector,
            )
            self.db.add(chunk)

        repo_file.total_chunks = len(raw_chunks)
        await self.db.flush()
