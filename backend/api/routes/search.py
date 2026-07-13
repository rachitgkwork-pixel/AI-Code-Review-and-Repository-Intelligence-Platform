from fastapi import APIRouter, Depends

from backend.auth.rbac import get_current_user
from backend.api.dependencies import get_search_service
from backend.schemas.search import SearchRequest, SearchResponse
from backend.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse)
async def semantic_search(
    payload: SearchRequest,
    _: object = Depends(get_current_user),
    search_svc: SearchService = Depends(get_search_service),
):
    results = await search_svc.search(
        query=payload.query,
        top_k=payload.top_k,
        repository_id=payload.repository_id,
    )
    return SearchResponse(query=payload.query, results=results, total=len(results))
