import asyncio
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from backend.auth.rbac import get_current_user
from backend.api.dependencies import get_indexing_service, get_repo_service
from backend.schemas.auth import TokenData
from backend.schemas.repository import RepositoryCreate, RepositoryResponse, RepositoryStatusResponse
from backend.services.indexing_service import IndexingService
from backend.services.repository_service import RepositoryService

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("/", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def add_repository(
    payload: RepositoryCreate,
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(get_current_user),
    repo_svc: RepositoryService = Depends(get_repo_service),
    indexing_svc: IndexingService = Depends(get_indexing_service),
):
    repo = await repo_svc.create(uuid.UUID(current_user.user_id), payload)
    # Kick off indexing in the background immediately after registration
    background_tasks.add_task(indexing_svc.index_repository, repo)
    return repo


@router.get("/", response_model=list[RepositoryResponse])
async def list_repositories(
    current_user: TokenData = Depends(get_current_user),
    repo_svc: RepositoryService = Depends(get_repo_service),
):
    return await repo_svc.list_for_user(uuid.UUID(current_user.user_id))


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    repo_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    repo_svc: RepositoryService = Depends(get_repo_service),
):
    repo = await repo_svc.get(repo_id, uuid.UUID(current_user.user_id))
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.get("/{repo_id}/status", response_model=RepositoryStatusResponse)
async def get_repository_status(
    repo_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    repo_svc: RepositoryService = Depends(get_repo_service),
):
    repo = await repo_svc.get(repo_id, uuid.UUID(current_user.user_id))
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repo_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    repo_svc: RepositoryService = Depends(get_repo_service),
):
    deleted = await repo_svc.delete(repo_id, uuid.UUID(current_user.user_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Repository not found")


@router.post("/{repo_id}/reindex", status_code=status.HTTP_202_ACCEPTED)
async def reindex_repository(
    repo_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(get_current_user),
    repo_svc: RepositoryService = Depends(get_repo_service),
    indexing_svc: IndexingService = Depends(get_indexing_service),
):
    repo = await repo_svc.get(repo_id, uuid.UUID(current_user.user_id))
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    background_tasks.add_task(indexing_svc.index_repository, repo)
    return {"detail": "Reindexing started"}
