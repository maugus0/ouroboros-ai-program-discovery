"""Program search and retrieval endpoints."""

from fastapi import APIRouter, Depends

from app.middleware.service_auth import require_service_token
from app.models.program import (
    ProgramDetailResponse,
    ProgramResponse,
    ProgramSearchRequest,
    ProgramSearchResponse,
)
from app.services.program_service import ProgramService
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/api/v1/programs", tags=["Programs"], dependencies=[Depends(require_service_token)])


@router.post("/search", response_model=ProgramSearchResponse)
async def search_programs(request: ProgramSearchRequest):
    """Search and rank programs based on filters and student profile."""
    service = ProgramService()
    result = await service.search_and_rank(request)

    programs = [
        ProgramResponse(
            id=p["id"],
            university_name=p.get("university_name", "Unknown"),
            program_name=p["program_name"],
            degree_type=p["degree_type"],
            field=p["field"],
            field_category=p.get("field_category"),
            description=p.get("description"),
            requirements=p.get("requirements"),
            deadline=p.get("deadline"),
            tuition_usd=p.get("tuition_usd"),
            duration_years=p.get("duration_years"),
            ranking_score=p.get("ranking_score"),
            source_url=p["source_url"],
            country=p.get("country"),
            university_ranking=p.get("university_ranking"),
            crawled_at=p.get("crawled_at"),
            match_score=p.get("match_score"),
        )
        for p in result["programs"]
    ]

    return ProgramSearchResponse(
        success=True,
        data=programs,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/{program_id}", response_model=ProgramDetailResponse)
async def get_program(program_id: str):
    """Get full program details including requirements."""
    service = ProgramService()
    program = await service.get_program_detail(program_id)

    if not program:
        raise NotFoundError("Program")

    response_data = ProgramResponse(
        id=program["id"],
        university_name=program.get("university_name", "Unknown"),
        program_name=program["program_name"],
        degree_type=program["degree_type"],
        field=program["field"],
        field_category=program.get("field_category"),
        description=program.get("description"),
        requirements=program.get("requirements"),
        deadline=program.get("deadline"),
        tuition_usd=program.get("tuition_usd"),
        duration_years=program.get("duration_years"),
        ranking_score=program.get("ranking_score"),
        source_url=program["source_url"],
        country=program.get("country"),
        university_ranking=program.get("university_ranking"),
        crawled_at=program.get("crawled_at"),
    )

    return ProgramDetailResponse(
        success=True,
        data=response_data,
        requirements=program.get("requirements_list", []),
    )
