"""LLM service with primary/fallback provider pattern."""

from typing import Any

from app.config import settings
from app.core.logging import get_logger
from app.llm.anthropic_client import call_anthropic
from app.llm.openai_client import call_openai
from app.llm.prompts import get_program_qa_prompt

logger = get_logger(__name__)


class LLMService:
    """Service for LLM-powered program discovery features.

    Uses OpenAI as primary provider and Anthropic as fallback.
    """

    async def answer_program_question(
        self,
        question: str,
        programs_context: list[dict[str, Any]],
        student_profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Answer a user's question about programs using LLM.

        Args:
            question: The user's question about programs.
            programs_context: List of relevant programs to consider.
            student_profile: Optional student profile for personalized answers.

        Returns:
            Dictionary with answer, sources, and metadata.
        """
        system_prompt = get_program_qa_prompt()
        user_content = self._build_qa_user_content(question, programs_context, student_profile)

        result = await self._call_with_fallback(system_prompt, user_content)

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
        result = await self._call_with_fallback(system_prompt, user_message)

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
    ) -> dict:
        """Call OpenAI first, fallback to Anthropic on failure."""
        if settings.OPENAI_API_KEY:
            try:
                return await call_openai(
                    system_prompt=system_prompt,
                    user_content=user_content,
                    json_mode=json_mode,
                )
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.warning("openai_call_failed_trying_anthropic", error=str(exc))

        if settings.ANTHROPIC_API_KEY:
            return await call_anthropic(
                system_prompt=system_prompt,
                user_content=user_content,
                json_mode=json_mode,
            )

        raise ValueError("No LLM API keys configured")

    def _build_qa_user_content(
        self,
        question: str,
        programs: list[dict[str, Any]],
        profile: dict[str, Any] | None,
    ) -> str:
        """Build the user content for Q&A."""
        parts = [f"Question: {question}\n"]

        if programs:
            parts.append("Relevant Programs:")
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
