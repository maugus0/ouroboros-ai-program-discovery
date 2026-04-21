"""LLM service with primary/fallback provider pattern."""

import time
from typing import Any

from app.config import settings
from app.core.logging import get_logger
from app.llm.anthropic_client import call_anthropic
from app.llm.openai_client import call_openai
from app.llm.prompts import get_program_qa_prompt
from app.repositories.llm_call_log_repo import LLMCallLogRepository

logger = get_logger(__name__)


class LLMService:
    """Service for LLM-powered program discovery features.

    Uses OpenAI as primary provider and Anthropic as fallback.
    """

    def __init__(self) -> None:
        """Initialize the LLM service."""
        self.log_repo = LLMCallLogRepository()

    async def answer_program_question(
        self,
        question: str,
        programs_context: list[dict[str, Any]],
        institutions_context: list[dict[str, Any]] | None = None,
        student_profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Answer a user's question about programs or institutions using LLM.

        Args:
            question: The user's question about programs or institutions.
            programs_context: List of relevant programs to consider.
            institutions_context: List of relevant institutions/universities (from QS rankings).
            student_profile: Optional student profile for personalized answers.

        Returns:
            Dictionary with answer, sources, and metadata.
        """
        system_prompt = get_program_qa_prompt()
        user_content = self._build_qa_user_content(
            question, programs_context, institutions_context or [], student_profile
        )

        result = await self._call_with_fallback(system_prompt, user_content, purpose="program_qa")

        return {
            "answer": result["content"].get("answer", ""),
            "programs_mentioned": result["content"].get("programs_mentioned", []),
            "follow_up_suggestions": result["content"].get("follow_up_suggestions", []),
            "confidence": result["content"].get("confidence", 0.0),
            "model": result["model"],
            "provider": result["provider"],
            "input_tokens": result["input_tokens"],
            "output_tokens": result["output_tokens"],
        }

    async def extract_search_intent(
        self,
        user_message: str,
    ) -> dict[str, Any]:
        """Extract search intent and filters from natural language.

        Args:
            user_message: The user's natural language query.

        Returns:
            Dictionary with extracted filters and intent.
        """
        system_prompt = self._get_intent_extraction_prompt()
        result = await self._call_with_fallback(system_prompt, user_message, purpose="intent_extraction")

        return {
            "intent": result["content"].get("intent", "search"),
            "filters": result["content"].get("filters", {}),
            "entities": result["content"].get("entities", {}),
            "model": result["model"],
            "provider": result["provider"],
        }

    async def _call_with_fallback(
        self,
        system_prompt: str,
        user_content: str,
        json_mode: bool = True,
        purpose: str = "general",
    ) -> dict:
        """Call OpenAI first, fallback to Anthropic on failure."""
        if settings.OPENAI_API_KEY:
            start_time = time.time()
            try:
                result = await call_openai(
                    system_prompt=system_prompt,
                    user_content=user_content,
                    json_mode=json_mode,
                )
                latency_ms = int((time.time() - start_time) * 1000)
                await self._log_call(
                    provider="openai",
                    model=result.get("model", "gpt-4o-mini"),
                    purpose=purpose,
                    input_tokens=result.get("input_tokens", 0),
                    output_tokens=result.get("output_tokens", 0),
                    latency_ms=latency_ms,
                    status="success",
                )
                return result
            except Exception as exc:  # pylint: disable=broad-exception-caught
                latency_ms = int((time.time() - start_time) * 1000)
                await self._log_call(
                    provider="openai",
                    model=settings.OPENAI_MODEL,
                    purpose=purpose,
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=latency_ms,
                    status="error",
                    error_message=str(exc),
                )
                logger.warning("openai_call_failed_trying_anthropic", error=str(exc))

        if settings.ANTHROPIC_API_KEY:
            start_time = time.time()
            try:
                result = await call_anthropic(
                    system_prompt=system_prompt,
                    user_content=user_content,
                    json_mode=json_mode,
                )
                latency_ms = int((time.time() - start_time) * 1000)
                await self._log_call(
                    provider="anthropic",
                    model=result.get("model", "claude-3-haiku"),
                    purpose=purpose,
                    input_tokens=result.get("input_tokens", 0),
                    output_tokens=result.get("output_tokens", 0),
                    latency_ms=latency_ms,
                    status="success",
                )
                return result
            except Exception as exc:  # pylint: disable=broad-exception-caught
                latency_ms = int((time.time() - start_time) * 1000)
                await self._log_call(
                    provider="anthropic",
                    model=settings.ANTHROPIC_MODEL,
                    purpose=purpose,
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=latency_ms,
                    status="error",
                    error_message=str(exc),
                )
                raise

        raise ValueError("No LLM API keys configured")

    async def _log_call(
        self,
        provider: str,
        model: str,
        purpose: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """Log an LLM call to the database."""
        try:
            await self.log_repo.create(
                provider=provider,
                model=model,
                purpose=purpose,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                status=status,
                error_message=error_message,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("failed_to_log_llm_call", error=str(exc))

    def _build_qa_user_content(
        self,
        question: str,
        programs: list[dict[str, Any]],
        institutions: list[dict[str, Any]],
        profile: dict[str, Any] | None,
    ) -> str:
        """Build the user content for Q&A."""
        parts = [f"Question: {question}\n"]

        if institutions:
            parts.append("Universities from QS World Rankings 2026 (real data from our database):\n")
            for inst in institutions:
                rank = inst.get("rank")
                rank_str = f"#{rank}" if rank else "Unranked"
                name = inst.get("name", "Unknown")
                country = inst.get("country", "Unknown")
                city = inst.get("city")
                location = f"{city}, {country}" if city else country

                parts.append(f"{rank_str}. {name}")
                parts.append(f"   Location: {location}")

                if inst.get("overall_score"):
                    parts.append(f"   Overall Score: {inst['overall_score']:.1f}/100")

                if inst.get("previous_rank"):
                    parts.append(f"   Previous Rank: {inst['previous_rank']}")

                details = []
                if inst.get("type") and inst["type"] != "unknown":
                    details.append(inst["type"].replace("_", " ").title())
                if inst.get("size") and inst["size"] != "unknown":
                    details.append(f"Size: {inst['size'].replace('_', ' ').title()}")
                if inst.get("research_output") and inst["research_output"] != "unknown":
                    details.append(f"Research: {inst['research_output'].replace('_', ' ').title()}")
                if details:
                    parts.append(f"   Type: {', '.join(details)}")

                indicators = inst.get("indicators", {})
                if indicators:
                    key_indicators = []
                    if indicators.get("academic_reputation"):
                        key_indicators.append(f"Academic Rep: {indicators['academic_reputation']:.1f}")
                    if indicators.get("employer_reputation"):
                        key_indicators.append(f"Employer Rep: {indicators['employer_reputation']:.1f}")
                    if indicators.get("citations_per_faculty"):
                        key_indicators.append(f"Citations: {indicators['citations_per_faculty']:.1f}")
                    if key_indicators:
                        parts.append(f"   Key Scores: {', '.join(key_indicators)}")

                parts.append("")

            parts.append(
                "IMPORTANT: Use ONLY the above real university data from our database. "
                "Present this data accurately with ranks and scores. Format the response clearly with ranks visible."
            )
            parts.append("")

        if programs:
            parts.append("Relevant Programs from our database:")
            for i, prog in enumerate(programs[:10], 1):
                parts.append(
                    f"{i}. {prog.get('program_name', 'Unknown')} at "
                    f"{prog.get('institution_name', 'Unknown')} "
                    f"({prog.get('country', 'Unknown')})"
                )
                if prog.get("degree_type"):
                    parts.append(f"   Degree: {prog['degree_type']}")
                if prog.get("tuition_usd"):
                    parts.append(f"   Tuition: ${prog['tuition_usd']:,}")
                if prog.get("deadline"):
                    parts.append(f"   Deadline: {prog['deadline']}")
            parts.append("")

        if profile:
            parts.append("Student Profile:")
            if profile.get("target_degree_level"):
                parts.append(f"- Target Degree: {profile['target_degree_level']}")
            if profile.get("field_of_interest"):
                parts.append(f"- Field of Interest: {profile['field_of_interest']}")
            if profile.get("gpa"):
                parts.append(f"- GPA: {profile['gpa']}")

        return "\n".join(parts)

    def _get_intent_extraction_prompt(self) -> str:
        """Get the system prompt for intent extraction."""
        return """You are an AI assistant that extracts search intent from user queries about academic programs.

Analyze the user's message and extract:
1. intent: One of "search", "compare", "details", "recommend", "general_question"
2. filters: Extracted search filters like:
   - field: Field of study
   - degree_type: bachelor, master, phd
   - country: Country name
   - max_tuition: Maximum tuition in USD
   - min_rank: Minimum university rank
   - max_rank: Maximum university rank
3. entities: Named entities like specific universities or programs mentioned

Respond in JSON format:
{
    "intent": "search",
    "filters": {
        "field": "Computer Science",
        "degree_type": "master",
        "country": "United States"
    },
    "entities": {
        "universities": ["MIT", "Stanford"],
        "programs": []
    }
}"""
