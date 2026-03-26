"""Weighted program ranking logic."""

import math
from datetime import date, datetime
from typing import Any, Optional

from app.config import settings
from app.core.logging import get_logger
from app.models.program import StudentProfileSummary
from app.models.ranking import RankingBreakdown

logger = get_logger(__name__)


class RankingService:
    """Rank programs using a configurable weighted scoring system."""

    def __init__(self, weights: dict[str, int] | None = None):
        self.weights = weights or settings.get_ranking_weights()

    def rank_programs(
        self,
        programs: list[dict[str, Any]],
        profile: Optional[StudentProfileSummary] = None,
    ) -> list[dict[str, Any]]:
        """Score and sort programs based on weighted criteria.

        Returns programs sorted by match_score descending.
        """
        scored = []
        for program in programs:
            breakdown = self._compute_breakdown(program, profile)
            program["match_score"] = breakdown.total_score
            program["ranking_breakdown"] = breakdown.model_dump()
            scored.append(program)

        scored.sort(key=lambda p: p.get("match_score", 0), reverse=True)
        return scored

    def _compute_breakdown(
        self,
        program: dict[str, Any],
        profile: Optional[StudentProfileSummary] = None,
    ) -> RankingBreakdown:
        """Compute the full scoring breakdown for a single program."""
        w = self.weights
        total_weight = sum(w.values()) or 100

        field_score = self._score_field_relevance(program, profile)
        req_score = self._score_requirement_match(program, profile)
        rank_score = self._score_university_ranking(program)
        deadline_score = self._score_deadline_proximity(program)
        tuition_score = self._score_tuition_affordability(program, profile)

        total = (
            (field_score * w["field_relevance"])
            + (req_score * w["requirement_match"])
            + (rank_score * w["university_ranking"])
            + (deadline_score * w["deadline_proximity"])
            + (tuition_score * w["tuition_affordability"])
        ) / total_weight

        return RankingBreakdown(
            field_relevance_score=round(field_score * 100, 1),
            requirement_match_score=round(req_score * 100, 1),
            university_ranking_score=round(rank_score * 100, 1),
            deadline_proximity_score=round(deadline_score * 100, 1),
            tuition_affordability_score=round(tuition_score * 100, 1),
            total_score=round(total * 100, 1),
        )

    @staticmethod
    def _score_field_relevance(program: dict[str, Any], profile: Optional[StudentProfileSummary]) -> float:
        """Score 0-1: how relevant the program field is to the student's interests."""
        if profile is None or not profile.target_field:
            return 0.5

        target = profile.target_field.lower()
        field = (program.get("field") or "").lower()
        name = (program.get("program_name") or "").lower()
        description = (program.get("description") or "").lower()

        target_words = set(target.split())
        combined_text = f"{field} {name} {description}"
        matches = sum(1 for word in target_words if word in combined_text)

        if not target_words:
            return 0.5

        return min(matches / len(target_words), 1.0)

    @staticmethod
    def _score_requirement_match(program: dict[str, Any], profile: Optional[StudentProfileSummary]) -> float:
        """Score 0-1: how many prerequisites the student meets."""
        if profile is None:
            return 0.5

        requirements = program.get("requirements") or {}
        if not requirements:
            return 0.8

        score = 1.0

        min_gpa = requirements.get("min_gpa")
        if min_gpa and profile.gpa:
            gpa_normalized = profile.gpa / (profile.gpa_scale or 4.0) * 4.0
            if gpa_normalized < float(min_gpa):
                score *= 0.5
            else:
                score *= 1.0

        prereqs = requirements.get("prerequisites", [])
        if prereqs and profile.prerequisites:
            student_courses = {c.lower() for c in profile.prerequisites}
            matched = sum(1 for p in prereqs if p.lower() in student_courses)
            score *= (matched / len(prereqs)) if prereqs else 1.0

        return min(score, 1.0)

    @staticmethod
    def _score_university_ranking(program: dict[str, Any]) -> float:
        """Score 0-1: higher ranked universities score higher (rank 1 = best)."""
        ranking = program.get("university_ranking")
        if ranking is None:
            return 0.3

        ranking = int(ranking)
        if ranking <= 0:
            return 0.3

        return max(1.0 - math.log(ranking) / math.log(500), 0.0)

    @staticmethod
    def _score_deadline_proximity(program: dict[str, Any]) -> float:
        """Score 0-1: programs with deadlines further out score higher."""
        deadline = program.get("deadline")
        if deadline is None:
            return 0.5

        if isinstance(deadline, str):
            try:
                deadline = datetime.strptime(deadline, "%Y-%m-%d").date()
            except ValueError:
                return 0.5

        if isinstance(deadline, datetime):
            deadline = deadline.date()

        days_until = (deadline - date.today()).days
        if days_until < 0:
            return 0.0
        if days_until > 365:
            return 1.0
        return days_until / 365.0

    @staticmethod
    def _score_tuition_affordability(program: dict[str, Any], profile: Optional[StudentProfileSummary]) -> float:
        """Score 0-1: lower tuition relative to budget scores higher."""
        tuition = program.get("tuition_usd")
        if tuition is None:
            return 0.5

        tuition = float(tuition)

        if profile and profile.budget_usd:
            budget = float(profile.budget_usd)
            if tuition <= budget:
                return 1.0
            if tuition <= budget * 1.5:
                return 0.5
            return 0.2

        if tuition <= 10000:
            return 1.0
        if tuition <= 30000:
            return 0.7
        if tuition <= 60000:
            return 0.4
        return 0.2
