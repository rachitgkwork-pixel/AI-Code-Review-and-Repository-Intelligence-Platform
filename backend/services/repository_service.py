import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.repository import Repository
from backend.schemas.repository import RepositoryCreate
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class RepositoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, owner_id: uuid.UUID, data: RepositoryCreate) -> Repository:
        repo = Repository(
            owner_id=owner_id,
            name=data.name,
            url=data.url,
            description=data.description,
            branch=data.branch,
            status="pending",
        )
        self.db.add(repo)
        await self.db.flush()
        logger.info("Created repository %s for user %s", repo.id, owner_id)
        return repo

    async def list_for_user(self, owner_id: uuid.UUID) -> list[Repository]:
        result = await self.db.execute(
            select(Repository).where(Repository.owner_id == owner_id)
        )
        return list(result.scalars().all())

    async def get(self, repo_id: uuid.UUID, owner_id: uuid.UUID) -> Repository | None:
        result = await self.db.execute(
            select(Repository).where(
                Repository.id == repo_id, Repository.owner_id == owner_id
            )
        )
        return result.scalar_one_or_none()

    async def delete(self, repo_id: uuid.UUID, owner_id: uuid.UUID) -> bool:
        repo = await self.get(repo_id, owner_id)
        if not repo:
            return False
        await self.db.delete(repo)
        logger.info("Deleted repository %s", repo_id)
        return True

    async def update_status(
        self,
        repo_id: uuid.UUID,
        status: str,
        *,
        total_files: int | None = None,
        indexed_files: int | None = None,
        local_path: str | None = None,
        error_message: str | None = None,
    ) -> Repository | None:
        repo = await self.db.get(Repository, repo_id)
        if not repo:
            return None
        repo.status = status
        if total_files is not None:
            repo.total_files = total_files
        if indexed_files is not None:
            repo.indexed_files = indexed_files
        if local_path is not None:
            repo.local_path = local_path
        if error_message is not None:
            repo.error_message = error_message
        await self.db.flush()
        return repo
