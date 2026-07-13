import uuid

from fastapi import APIRouter, Depends, HTTPException

from backend.auth.rbac import get_current_user
from backend.api.dependencies import get_review_service
from backend.schemas.auth import TokenData
from backend.schemas.review import FileReviewRequest, RepositoryReviewRequest, ReviewResponse
from backend.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _to_response(review) -> ReviewResponse:
    return ReviewResponse(
        review_id=review.id,
        repository_id=review.repository_id,
        file_path=review.file_path,
        review_type=review.review_type,
        status=review.status,
        issues=review.results or [],
        llm_model=review.llm_model,
        created_at=review.created_at,
        completed_at=review.completed_at,
    )


@router.post("/file", response_model=ReviewResponse)
async def review_file(
    payload: FileReviewRequest,
    current_user: TokenData = Depends(get_current_user),
    review_svc: ReviewService = Depends(get_review_service),
):
    review = await review_svc.review_file(
        repository_id=payload.repository_id,
        file_path=payload.file_path,
        user_id=uuid.UUID(current_user.user_id),
    )
    return _to_response(review)


@router.post("/repository", response_model=ReviewResponse)
async def review_repository(
    payload: RepositoryReviewRequest,
    current_user: TokenData = Depends(get_current_user),
    review_svc: ReviewService = Depends(get_review_service),
):
    review = await review_svc.review_repository(
        repository_id=payload.repository_id,
        user_id=uuid.UUID(current_user.user_id),
    )
    return _to_response(review)
