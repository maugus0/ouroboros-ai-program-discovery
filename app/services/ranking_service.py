"""Service layer for program ranking and scoring."""

from datetime import date
from decimal import Decimal
from typing import Any

from app.config import settings
from app.core.logging import get_logger
from app.models import (
    ProgramRankingRequest,
    ProgramResponse,
    ProgramSearchRequest,
    RankedProgram,
)
from app.repositories import InstitutionRankingRepository, ProgramRepository

logger = get_logger(__name__)


class RankingService:
    """Business logic for ranking programs based on student profile."""

    def __init__(
        self,
        program_repo: ProgramRepository | None = None,
        ranking_repo: InstitutionRankingRepository | None = None,
    ):
        self._program_repo = program_repo or ProgramRepository()
        self._ranking_repo = ranking_repo or InstitutionRankingRepository()

    async def rank_programs(self, request: ProgramRankingRequest) -> list[RankedProgram]:
        """Rank programs based on student profile and preferences."""
        search_request = ProgramSearchRequest(
            query=None,
            field=request.target_field,
            degree_type=request.target_degree,
            country=request.country_preferences[0] if request.country_preferences else None,
            min_rank=None,
            max_rank=None,
            max_tuition_usd=request.max_tuition_usd,
            deadline_after=request.deadline_cutoff,
            page=1,
            page_size=request.limit * 3,
        )

        result = await self._program_repo.search(search_request)
        programs = result.items

        ranked = []
        for program in programs:
            score, breakdown, reasons = await self._calculate_score(program, request.student_profile, request)
            ranked.append(
                RankedProgram(
                    **program.model_dump(),
                    overall_score=score,
                    score_breakdown=breakdown,
                    match_reasons=reasons,
                )
            )

        ranked.sort(key=lambda p: p.overall_score, reverse=True)
        return ranked[: request.limit]

    async def _calculate_score(
        self,
        program: ProgramResponse,
        student_profile: dict[str, Any],
        request: ProgramRankingRequest,
    ) -> tuple[float, dict[str, float], list[str]]:
        """Calculate the overall score for a program."""
        weights = settings.get_ranking_weights()
        breakdown: dict[str, float] = {}
        reasons: list[str] = []

        field_score = self._score_field_relevance(program, request.target_field)
        breakdown["field_relevance"] = field_score
        if field_score > 80:
            reasons.append(f"Strong match for {request.target_field}")

        req_score = self._score_requirement_match(program, student_profile)
        breakdown["requirement_match"] = req_score
        if req_score > 80:
            reasons.append("Requirements align well with your profile")

        rank_score = self._score_university_ranking(program.institution_rank)
        breakdown["university_ranking"] = rank_score
        if rank_score > 80:
            reasons.append(f"Top-ranked institution (#{program.institution_rank})")

        deadline_score = self._score_deadline_proximity(program.deadline)
        breakdown["deadline_proximity"] = deadline_score
        if deadline_score > 80 and program.deadline:
            reasons.append(f"Application deadline: {program.deadline}")

        tuition_score = self._score_tuition_affordability(program.tuition_usd, request.max_tuition_usd)
        breakdown["tuition_affordability"] = tuition_score
        if tuition_score > 80:
            reasons.append("Within your budget")

        total_weight = sum(weights.values())
        overall_score = (
            field_score * weights["field_relevance"]
            + req_score * weights["requirement_match"]
            + rank_score * weights["university_ranking"]
            + deadline_score * weights["deadline_proximity"]
            + tuition_score * weights["tuition_affordability"]
        ) / total_weight

        return round(overall_score, 2), breakdown, reasons

    def _score_field_relevance(self, program: ProgramResponse, target_field: str) -> float:
        """Score how relevant the program field is to the target field."""
        target_lower = target_field.lower()
        program_field_lower = program.field.lower()

        if target_lower == program_field_lower:
            return 100.0

        if target_lower in program_field_lower or program_field_lower in target_lower:
            return 85.0

        target_words = set(target_lower.split())
        program_words = set(program_field_lower.split())
        overlap = len(target_words & program_words)
        if overlap > 0:
            return min(70.0 + overlap * 10, 90.0)

        if program.field_category and target_lower in program.field_category.lower():
            return 60.0

        return 30.0

    def _score_requirement_match(self, program: ProgramResponse, student_profile: dict[str, Any]) -> float:
        """Score how well the student meets program requirements."""
        if not program.requirements:
            return 70.0

        total_reqs = 0
        met_reqs = 0

        requirements = program.requirements
        if isinstance(requirements, dict):
            if "gpa" in requirements and "gpa" in student_profile:
                total_reqs += 1
                if float(student_profile.get("gpa", 0)) >= float(requirements["gpa"]):
                    met_reqs += 1

            for test in ["gre", "gmat", "toefl", "ielts"]:
                if test in requirements and test in student_profile:
                    total_reqs += 1
                    if float(student_profile.get(test, 0)) >= float(requirements[test]):
                        met_reqs += 1

        if total_reqs == 0:
            return 70.0

        return round((met_reqs / total_reqs) * 100, 2)

    def _score_university_ranking(self, rank: int | None) -> float:
        """Score based on university ranking (lower rank = higher score)."""
        if rank is None:
            return 50.0

        return self._normalize_rank(rank)

    def _normalize_rank(self, rank: int) -> float:
        """Convert rank to 0-100 score. Rank 1 = 100, Rank 1500+ = ~20."""
        if rank <= 0:
            return 50.0
        if rank == 1:
            return 100.0
        if rank <= 10:
            return 95.0 + (10 - rank) * 0.5
        if rank <= 50:
            return 85.0 + (50 - rank) * 0.25
        if rank <= 100:
            return 75.0 + (100 - rank) * 0.2
        if rank <= 200:
            return 65.0 + (200 - rank) * 0.1
        if rank <= 500:
            return 50.0 + (500 - rank) * 0.05
        if rank <= 1000:
            return 35.0 + (1000 - rank) * 0.03
        return max(20.0, 35.0 - (rank - 1000) * 0.01)

    def _score_deadline_proximity(self, deadline: date | None) -> float:
        """Score based on deadline proximity (further deadline = higher score)."""
        if deadline is None:
            return 70.0

        today = date.today()
        if deadline < today:
            return 0.0

        days_until = (deadline - today).days

        if days_until >= 180:
            return 100.0
        if days_until >= 90:
            return 85.0
        if days_until >= 60:
            return 70.0
        if days_until >= 30:
            return 55.0
        if days_until >= 14:
            return 40.0
        return 25.0

    def _score_tuition_affordability(self, tuition_usd: Decimal | None, max_budget: Decimal | None) -> float:
        """Score based on tuition affordability."""
        if tuition_usd is None:
            return 60.0

        if max_budget is None:
            return 70.0

        tuition = float(tuition_usd)
        budget = float(max_budget)

        if tuition <= budget * 0.5:
            return 100.0
        if tuition <= budget * 0.75:
            return 90.0
        if tuition <= budget:
            return 80.0
        if tuition <= budget * 1.25:
            return 50.0
        return 20.0
