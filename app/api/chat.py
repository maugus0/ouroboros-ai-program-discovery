"""Conversational API endpoints for program Q&A."""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.llm import LLMService
from app.middleware import require_service_token
from app.services import ProgramService

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


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


@router.post(
    "/ask",
    response_model=ProgramQuestionResponse,
    dependencies=[Depends(require_service_token)],
)
async def ask_about_programs(
    request: ProgramQuestionRequest,
    llm_service: LLMService = Depends(get_llm_service),
    program_service: ProgramService = Depends(get_program_service),
) -> ProgramQuestionResponse:
    """Ask a question about academic programs.

    This endpoint uses LLM to answer natural language questions about programs,
    considering relevant programs from the database and optional student profile.
    """
    logger.info("program_question_received", question=request.question[:100])

    programs_context = []
    if request.filters or request.question:
        from app.models import ProgramSearchRequest

        search_request = ProgramSearchRequest(
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
        result = await program_service.search_programs(search_request)
        programs_context = [p.model_dump() for p in result.items]

    response = await llm_service.answer_program_question(
        question=request.question,
        programs_context=programs_context,
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
