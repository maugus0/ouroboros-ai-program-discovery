"""Program API endpoints."""

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query

from app.core.logging import get_logger
from app.middleware import require_service_token
from app.models import (
    DegreeType,
    PaginatedResponse,
    ProgramMode,
    ProgramRankingRequest,
    ProgramResponse,
    ProgramSearchRequest,
    RankedProgram,
)
from app.services import ProgramService, RankingService

logger = get_logger(__name__)

router = APIRouter(prefix="/programs", tags=["Programs"])


def get_program_service() -> ProgramService:
    return ProgramService()


def get_ranking_service() -> RankingService:
    return RankingService()


@router.get(
    "",
    response_model=PaginatedResponse[ProgramResponse],
    dependencies=[Depends(require_service_token)],
)
async def search_programs(
    query: str | None = Query(None, description="Search by program name or description"),
    institution_id: str | None = Query(None, description="Filter by institution"),
    degree_type: DegreeType | None = Query(None, description="Filter by degree type"),
    field: str | None = Query(None, description="Filter by field of study"),
    field_category: str | None = Query(None, description="Filter by field category"),
    country: str | None = Query(None, description="Filter by country"),
    min_rank: int | None = Query(None, ge=1, description="Min university rank"),
    max_rank: int | None = Query(None, ge=1, description="Max university rank"),
    max_tuition_usd: Decimal | None = Query(None, ge=0, description="Max tuition in USD"),
    deadline_after: date | None = Query(None, description="Deadline after date"),
    deadline_before: date | None = Query(None, description="Deadline before date"),
    language: str | None = Query(None, description="Filter by language"),
    mode: ProgramMode | None = Query(None, description="Filter by mode"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ProgramService = Depends(get_program_service),
) -> PaginatedResponse[ProgramResponse]:
    """Search programs with filters and pagination."""
    request = ProgramSearchRequest(
        query=query,
        institution_id=institution_id,
        degree_type=degree_type,
        field=field,
        field_category=field_category,
        country=country,
        min_rank=min_rank,
        max_rank=max_rank,
        max_tuition_usd=max_tuition_usd,
        deadline_after=deadline_after,
        deadline_before=deadline_before,
        language=language,
        mode=mode,
        page=page,
        page_size=page_size,
    )
    return await service.search_programs(request)


@router.get(
    "/fields",
    response_model=list[str],
    dependencies=[Depends(require_service_token)],
)
async def get_fields(
    service: ProgramService = Depends(get_program_service),
) -> list[str]:
    """Get list of all unique fields."""
    return await service.get_all_fields()


@router.get(
    "/field-categories",
    response_model=list[str],
    dependencies=[Depends(require_service_token)],
)
async def get_field_categories(
    service: ProgramService = Depends(get_program_service),
) -> list[str]:
    """Get list of all unique field categories."""
    return await service.get_all_field_categories()


@router.get(
    "/count",
    response_model=dict,
    dependencies=[Depends(require_service_token)],
)
async def get_program_count(
    service: ProgramService = Depends(get_program_service),
) -> dict:
    """Get total count of active programs."""
    count = await service.get_program_count()
    return {"count": count}


@router.post(
    "/rank",
    response_model=list[RankedProgram],
    dependencies=[Depends(require_service_token)],
)
async def rank_programs(
    request: ProgramRankingRequest,
    service: RankingService = Depends(get_ranking_service),
) -> list[RankedProgram]:
    """Rank programs based on student profile and preferences."""
    return await service.rank_programs(request)


@router.get(
    "/{program_id}",
    response_model=ProgramResponse,
    dependencies=[Depends(require_service_token)],
)
async def get_program(
    program_id: str,
    service: ProgramService = Depends(get_program_service),
) -> ProgramResponse:
    """Get a program by ID with institution details."""
    return await service.get_program(program_id)


@router.get(
    "/{program_id}/requirements",
    dependencies=[Depends(require_service_token)],
)
async def get_program_requirements(
    program_id: str,
    service: ProgramService = Depends(get_program_service),
):
    """Get all requirements for a program."""
    return await service.get_program_requirements(program_id)
