"""Conversational API endpoints for program Q&A."""

import re
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.llm import LLMService
from app.middleware import require_service_token
from app.services import InstitutionService, ProgramService

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

# Patterns to detect institution/ranking queries
INSTITUTION_PATTERNS = [
    r"\btop\s+\d+\s+(uni|univ|universit)",
    r"\bqs\s+(world\s+)?rank",
    r"\brand?king",
    r"\buniversit(y|ies)\b",
    r"\binstitution",
    r"\bcollege",
    r"\btop\s+\d+\s+school",
    r"\blist\s+of\s+(uni|univ|universit|institution|school)",
]

# Patterns for program-specific queries
PROGRAM_PATTERNS = [
    r"\bprogram",
    r"\bcourse",
    r"\bdegree",
    r"\bmaster",
    r"\bphd\b",
    r"\bbachelor",
    r"\bmba\b",
    r"\btuition",
    r"\bdeadline",
    r"\brequirement",
    r"\badmission",
]


def _is_institution_query(question: str) -> bool:
    """Detect if the question is primarily about institutions/rankings."""
    q_lower = question.lower()
    institution_match = any(re.search(p, q_lower) for p in INSTITUTION_PATTERNS)
    program_match = any(re.search(p, q_lower) for p in PROGRAM_PATTERNS)
    return institution_match and not program_match


def _extract_limit_from_question(question: str) -> int:
    """Extract numeric limit from question like 'top 100 universities'."""
    match = re.search(r"\btop\s+(\d+)", question.lower())
    if match:
        return min(int(match.group(1)), 100)
    return 20


def _extract_country_from_question(question: str) -> str | None:
    """Extract country from question."""
    q_lower = question.lower()
    countries = {
        "singapore": "Singapore",
        "usa": "United States",
        "united states": "United States",
        "uk": "United Kingdom",
        "united kingdom": "United Kingdom",
        "germany": "Germany",
        "australia": "Australia",
        "canada": "Canada",
        "japan": "Japan",
        "china": "China",
        "india": "India",
        "france": "France",
        "switzerland": "Switzerland",
        "netherlands": "Netherlands",
        "sweden": "Sweden",
        "south korea": "South Korea",
        "korea": "South Korea",
        "hong kong": "Hong Kong",
    }
    for key, value in countries.items():
        if key in q_lower:
            return value
    return None


class ProgramQuestionRequest(BaseModel):
    """Request model for program questions."""

    question: str = Field(..., description="The user's question about programs")
    filters: dict[str, Any] = Field(default_factory=dict, description="Optional filters")
    student_profile: dict[str, Any] | None = Field(None, description="Optional student profile")
    limit: int = Field(10, ge=1, le=50, description="Max programs to consider")


class ProgramQuestionResponse(BaseModel):
    """Response model for program questions."""

    answer: str
    programs_mentioned: list[str] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    model: str
    provider: str


class IntentExtractionRequest(BaseModel):
    """Request model for intent extraction."""

    message: str = Field(..., description="The user's natural language message")


class IntentExtractionResponse(BaseModel):
    """Response model for intent extraction."""

    intent: str
    filters: dict[str, Any] = Field(default_factory=dict)
    entities: dict[str, Any] = Field(default_factory=dict)


def get_llm_service() -> LLMService:
    return LLMService()


def get_program_service() -> ProgramService:
    return ProgramService()


def get_institution_service() -> InstitutionService:
    return InstitutionService()


@router.post(
    "/ask",
    response_model=ProgramQuestionResponse,
    dependencies=[Depends(require_service_token)],
)
async def ask_about_programs(
    request: ProgramQuestionRequest,
    llm_service: LLMService = Depends(get_llm_service),
    program_service: ProgramService = Depends(get_program_service),
    institution_service: InstitutionService = Depends(get_institution_service),
) -> ProgramQuestionResponse:
    """Ask a question about academic programs or institutions.

    This endpoint uses real database data for institution/ranking queries,
    and LLM to answer natural language questions about programs.
    """
    logger.info("program_question_received", question=request.question[:100])

    programs_context: list[dict[str, Any]] = []
    institutions_context: list[dict[str, Any]] = []

    is_inst_query = _is_institution_query(request.question)

    if is_inst_query:
        from app.models import InstitutionSearchRequest

        limit = _extract_limit_from_question(request.question)
        country = _extract_country_from_question(request.question)
        logger.info(
            "institution_query_detected",
            limit=limit,
            country=country,
        )

        inst_search = InstitutionSearchRequest(
            query=request.filters.get("query"),
            country=country or request.filters.get("country"),
            institution_type=None,
            min_rank=None,
            max_rank=limit if "top" in request.question.lower() else None,
            ranking_source=None,
            ranking_year=None,
            page=1,
            page_size=min(limit, 100),
        )
        inst_result = await institution_service.search_institutions(inst_search)

        # Fetch detailed ranking info for each institution
        for inst in inst_result.items:
            rankings = await institution_service.get_institution_rankings(inst.id)
            qs_ranking = next((r for r in rankings if r.ranking_source.value == "qs_world"), None)

            inst_data: dict[str, Any] = {
                "rank": inst.best_rank,
                "name": inst.name,
                "country": inst.country,
                "city": inst.city,
                "type": inst.institution_type.value if inst.institution_type else None,
                "size": inst.size.value if inst.size and inst.size.value != "unknown" else None,
                "focus": inst.focus.value if inst.focus and inst.focus.value != "unknown" else None,
                "research_output": (
                    inst.research_output.value
                    if inst.research_output and inst.research_output.value != "unknown"
                    else None
                ),
            }

            if qs_ranking:
                inst_data["overall_score"] = float(qs_ranking.overall_score) if qs_ranking.overall_score else None
                inst_data["previous_rank"] = qs_ranking.previous_rank_display
                inst_data["ranking_year"] = qs_ranking.ranking_year
                if qs_ranking.raw_metadata:
                    inst_data["indicators"] = qs_ranking.raw_metadata

            institutions_context.append(inst_data)

        logger.info("institutions_found", count=len(institutions_context))

    if not is_inst_query or request.filters:
        from app.models import ProgramSearchRequest

        prog_search = ProgramSearchRequest(
            query=request.filters.get("query") or request.question[:50],
            field=request.filters.get("field"),
            degree_type=request.filters.get("degree_type"),
            country=request.filters.get("country"),
            min_rank=None,
            max_rank=None,
            max_tuition_usd=None,
            page=1,
            page_size=request.limit,
        )
        prog_result = await program_service.search_programs(prog_search)
        programs_context = [p.model_dump() for p in prog_result.items]

    response = await llm_service.answer_program_question(
        question=request.question,
        programs_context=programs_context,
        institutions_context=institutions_context,
        student_profile=request.student_profile,
    )

    return ProgramQuestionResponse(
        answer=response["answer"],
        programs_mentioned=response["programs_mentioned"],
        follow_up_suggestions=response["follow_up_suggestions"],
        confidence=response["confidence"],
        model=response["model"],
        provider=response["provider"],
    )


@router.post(
    "/extract-intent",
    response_model=IntentExtractionResponse,
    dependencies=[Depends(require_service_token)],
)
async def extract_search_intent(
    request: IntentExtractionRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> IntentExtractionResponse:
    """Extract search intent and filters from natural language.

    This endpoint parses a user's natural language query and extracts
    structured search filters and intent for program discovery.
    """
    logger.info("intent_extraction_requested", message=request.message[:100])

    result = await llm_service.extract_search_intent(request.message)

    return IntentExtractionResponse(
        intent=result["intent"],
        filters=result["filters"],
        entities=result["entities"],
    )
