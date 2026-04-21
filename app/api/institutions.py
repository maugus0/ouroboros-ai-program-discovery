"""Institution API endpoints."""

from fastapi import APIRouter, Depends, Query

from app.core.logging import get_logger
from app.middleware import require_service_token
from app.models import (
    InstitutionResponse,
    InstitutionSearchRequest,
    InstitutionType,
    PaginatedResponse,
)
from app.services import InstitutionService

logger = get_logger(__name__)

router = APIRouter(prefix="/institutions", tags=["Institutions"])


def get_institution_service() -> InstitutionService:
    return InstitutionService()


@router.get(
    "",
    response_model=PaginatedResponse[InstitutionResponse],
    dependencies=[Depends(require_service_token)],
)
async def search_institutions(
    query: str | None = Query(None, description="Search by institution name"),
    country: str | None = Query(None, description="Filter by country"),
    institution_type: InstitutionType | None = Query(None, description="Filter by type"),
    min_rank: int | None = Query(None, ge=1, description="Minimum rank position"),
    max_rank: int | None = Query(None, ge=1, description="Maximum rank position"),
    ranking_source: str | None = Query(None, description="Filter by ranking source"),
    ranking_year: int | None = Query(None, description="Filter by ranking year"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: InstitutionService = Depends(get_institution_service),
) -> PaginatedResponse[InstitutionResponse]:
    """Search institutions with filters and pagination."""
    request = InstitutionSearchRequest(
        query=query,
        country=country,
        institution_type=institution_type,
        min_rank=min_rank,
        max_rank=max_rank,
        ranking_source=ranking_source,
        ranking_year=ranking_year,
        page=page,
        page_size=page_size,
    )
    return await service.search_institutions(request)


@router.get(
    "/countries",
    response_model=list[str],
    dependencies=[Depends(require_service_token)],
)
async def get_countries(
    service: InstitutionService = Depends(get_institution_service),
) -> list[str]:
    """Get list of all countries with institutions."""
    return await service.get_all_countries()


@router.get(
    "/count",
    response_model=dict,
    dependencies=[Depends(require_service_token)],
)
async def get_institution_count(
    service: InstitutionService = Depends(get_institution_service),
) -> dict:
    """Get total count of active institutions."""
    count = await service.get_institution_count()
    return {"count": count}


@router.get(
    "/{institution_id}",
    response_model=InstitutionResponse,
    dependencies=[Depends(require_service_token)],
)
async def get_institution(
    institution_id: str,
    service: InstitutionService = Depends(get_institution_service),
) -> InstitutionResponse:
    """Get an institution by ID with ranking information."""
    return await service.get_institution(institution_id)


@router.get(
    "/{institution_id}/rankings",
    dependencies=[Depends(require_service_token)],
)
async def get_institution_rankings(
    institution_id: str,
    service: InstitutionService = Depends(get_institution_service),
):
    """Get all rankings for an institution."""
    return await service.get_institution_rankings(institution_id)
