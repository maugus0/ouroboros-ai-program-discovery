"""ReAct-style ranking decision engine for program discovery.

This module implements the Reason-Act-Observe pattern for transparent program ranking:
- Reason: Evaluate each program against student profile using 4 dimensions
- Act: Score and rank programs, mark decisions (recommend/consider/filter_out)
- Observe: Generate decision trace and evidence for each program
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any


class ProgramDecision(str, Enum):
    """Decision outcome for a program evaluation."""

    RECOMMEND = "recommend"
    CONSIDER = "consider"
    FILTER_OUT = "filter_out"


@dataclass
class ProgramMatchScores:
    """Multi-dimensional match scores for a program."""

    field_relevance: float = 0.0
    academic_fit: float = 0.0
    deadline_viability: float = 0.0
    university_tier: float = 0.0
    tuition_affordability: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "field_relevance": round(self.field_relevance, 3),
            "academic_fit": round(self.academic_fit, 3),
            "deadline_viability": round(self.deadline_viability, 3),
            "university_tier": round(self.university_tier, 3),
            "tuition_affordability": round(self.tuition_affordability, 3),
        }


@dataclass
class ProgramEvidence:
    """Evidence strings explaining each dimension score."""

    field_relevance: str = ""
    academic_fit: str = ""
    deadline_viability: str = ""
    university_tier: str = ""
    tuition_affordability: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "field_relevance": self.field_relevance,
            "academic_fit": self.academic_fit,
            "deadline_viability": self.deadline_viability,
            "university_tier": self.university_tier,
            "tuition_affordability": self.tuition_affordability,
        }


@dataclass
class ProgramDecisionEntry:
    """Decision trace entry for a single program."""

    decision: ProgramDecision
    reasons: list[str] = field(default_factory=list)
    composite_score: float = 0.0
    rank: int | None = None
    match_scores: ProgramMatchScores = field(default_factory=ProgramMatchScores)
    evidence: ProgramEvidence = field(default_factory=ProgramEvidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reasons": self.reasons,
            "composite_score": round(self.composite_score, 3),
            "rank": self.rank,
            "match_scores": self.match_scores.to_dict(),
            "evidence": self.evidence.to_dict(),
        }


DEFAULT_WEIGHTS = {
    "field_relevance": 0.35,
    "academic_fit": 0.30,
    "deadline_viability": 0.10,
    "university_tier": 0.15,
    "tuition_affordability": 0.10,
}

RECOMMEND_THRESHOLD = 0.70
CONSIDER_THRESHOLD = 0.50


def apply_react_ranking_pattern(
    programs: list[dict[str, Any]],
    student_profile: dict[str, Any],
    weights: dict[str, float] | None = None,
    recommend_threshold: float = RECOMMEND_THRESHOLD,
    consider_threshold: float = CONSIDER_THRESHOLD,
) -> dict[str, Any]:
    """Apply Reason-Act-Observe pattern for program ranking.

    This function evaluates each program against the student profile using a
    multi-dimensional scoring approach, generating a complete decision trace
    with evidence for each recommendation.

    Args:
        programs: List of program dictionaries to evaluate.
        student_profile: Student profile with academic credentials.
        weights: Optional custom weights for each dimension.
        recommend_threshold: Minimum composite score to recommend (default 0.70).
        consider_threshold: Minimum composite score to consider (default 0.50).

    Returns:
        Dictionary containing:
        - react_decision_trace: Per-program decision details
        - ranked_programs: Programs sorted by composite score
        - filters_applied: List of applied filters with counts
        - summary: High-level statistics
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    react_decision_trace: dict[str, ProgramDecisionEntry] = {}
    evaluated_programs: list[dict[str, Any]] = []
    filters_applied: list[str] = []
    total_filtered = 0

    for program in programs:
        program_id = program.get("id") or program.get("program_id", "unknown")

        scores, evidence = _calculate_multi_dimensional_scores(program, student_profile)

        composite_score = _calculate_composite_score(scores, weights)

        decision, reasons = _determine_decision(
            scores, evidence, composite_score, recommend_threshold, consider_threshold
        )

        entry = ProgramDecisionEntry(
            decision=decision,
            reasons=reasons,
            composite_score=composite_score,
            match_scores=scores,
            evidence=evidence,
        )

        react_decision_trace[program_id] = entry

        if decision == ProgramDecision.FILTER_OUT:
            total_filtered += 1
        else:
            evaluated_programs.append(
                {
                    "program_id": program_id,
                    "program_name": program.get("program_name", "Unknown Program"),
                    "university": program.get("institution_name", "Unknown University"),
                    "country": program.get("institution_country") or program.get("country"),
                    "degree_type": program.get("degree_type"),
                    "field": program.get("field"),
                    "deadline": str(program.get("deadline")) if program.get("deadline") else None,
                    "tuition_usd": float(program.get("tuition_usd") or 0),
                    "institution_rank": program.get("institution_rank"),
                    "composite_score": composite_score,
                    "decision": decision.value,
                    "match_scores": scores.to_dict(),
                    "evidence": evidence.to_dict(),
                    "reasons": reasons,
                }
            )

    evaluated_programs.sort(key=lambda p: p["composite_score"], reverse=True)
    for rank, prog in enumerate(evaluated_programs, 1):
        prog["rank"] = rank
        program_id = prog["program_id"]
        if program_id in react_decision_trace:
            react_decision_trace[program_id].rank = rank

    filters_applied = _build_filters_applied_summary(
        total_programs=len(programs),
        total_filtered=total_filtered,
        student_profile=student_profile,
        recommend_threshold=recommend_threshold,
    )

    recommended_count = sum(1 for p in evaluated_programs if p["decision"] == "recommend")
    considered_count = sum(1 for p in evaluated_programs if p["decision"] == "consider")

    return {
        "react_decision_trace": {k: v.to_dict() for k, v in react_decision_trace.items()},
        "ranked_programs": evaluated_programs,
        "filters_applied": filters_applied,
        "summary": {
            "total_programs_evaluated": len(programs),
            "total_recommended": recommended_count,
            "total_considered": considered_count,
            "total_filtered_out": total_filtered,
            "recommend_threshold": recommend_threshold,
            "consider_threshold": consider_threshold,
            "weights_used": weights,
        },
    }


def _calculate_multi_dimensional_scores(
    program: dict[str, Any],
    student_profile: dict[str, Any],
) -> tuple[ProgramMatchScores, ProgramEvidence]:
    """Calculate 4-dimension scores with evidence for a program."""
    scores = ProgramMatchScores()
    evidence = ProgramEvidence()

    field_score, field_evidence = _score_field_relevance(program, student_profile)
    scores.field_relevance = field_score
    evidence.field_relevance = field_evidence

    academic_score, academic_evidence = _score_academic_fit(program, student_profile)
    scores.academic_fit = academic_score
    evidence.academic_fit = academic_evidence

    deadline_score, deadline_evidence = _score_deadline_viability(program)
    scores.deadline_viability = deadline_score
    evidence.deadline_viability = deadline_evidence

    tier_score, tier_evidence = _score_university_tier(program)
    scores.university_tier = tier_score
    evidence.university_tier = tier_evidence

    tuition_score, tuition_evidence = _score_tuition_affordability(program, student_profile)
    scores.tuition_affordability = tuition_score
    evidence.tuition_affordability = tuition_evidence

    return scores, evidence


def _score_field_relevance(
    program: dict[str, Any],
    student_profile: dict[str, Any],
) -> tuple[float, str]:
    """Score how relevant the program field is to the student's interest."""
    program_field = (program.get("field") or "").lower()
    program_category = (program.get("field_category") or "").lower()

    student_field = (student_profile.get("field_of_interest") or student_profile.get("target_field") or "").lower()

    if not student_field:
        return 0.70, "No target field specified in student profile"

    if not program_field:
        return 0.50, "Program field information not available"

    if program_field == student_field:
        return 1.0, f"Perfect match: program field '{program.get('field')}' matches student interest"

    if student_field in program_field or program_field in student_field:
        return (
            0.90,
            f"Strong match: '{program.get('field')}' closely aligns with '{student_profile.get('field_of_interest')}'",
        )

    student_words = set(student_field.split())
    program_words = set(program_field.split())
    overlap = len(student_words & program_words)

    if overlap >= 2:
        return 0.80, f"Good overlap: {overlap} common terms between fields"
    if overlap == 1:
        return 0.65, "Partial overlap: 1 common term between fields"

    if student_field in program_category:
        return 0.60, f"Category match: program in '{program.get('field_category')}' category"

    return (
        0.30,
        f"Limited relevance: '{program.get('field')}' differs from target '{student_profile.get('field_of_interest')}'",
    )


def _score_academic_fit(
    program: dict[str, Any],
    student_profile: dict[str, Any],
) -> tuple[float, str]:
    """Score how well the student meets program requirements."""
    requirements = program.get("requirements") or {}
    if not requirements:
        return 0.70, "No specific requirements listed for this program"

    total_checks = 0
    passed_checks = 0
    evidence_parts = []

    student_gpa = student_profile.get("gpa")
    req_gpa = requirements.get("gpa")
    if req_gpa is not None:
        total_checks += 1
        try:
            req_gpa_float = float(req_gpa)
            if student_gpa is not None:
                student_gpa_float = float(student_gpa)
                if student_gpa_float >= req_gpa_float:
                    passed_checks += 1
                    margin = student_gpa_float - req_gpa_float
                    if margin >= 0.3:
                        evidence_parts.append(
                            f"GPA {student_gpa_float} exceeds minimum {req_gpa_float} by {margin:.1f}"
                        )
                    else:
                        evidence_parts.append(f"GPA {student_gpa_float} meets minimum {req_gpa_float}")
                else:
                    evidence_parts.append(f"GPA {student_gpa_float} below minimum {req_gpa_float}")
            else:
                evidence_parts.append(f"Student GPA unknown; program requires {req_gpa_float}")
        except (TypeError, ValueError):
            pass

    test_mappings = [
        ("toefl", "TOEFL"),
        ("ielts", "IELTS"),
        ("gre", "GRE"),
        ("gmat", "GMAT"),
    ]

    for test_key, test_name in test_mappings:
        req_score = requirements.get(test_key)
        if req_score is not None:
            total_checks += 1
            try:
                req_score_float = float(req_score)
                student_score = student_profile.get(test_key)
                if student_score is not None:
                    student_score_float = float(student_score)
                    if student_score_float >= req_score_float:
                        passed_checks += 1
                        evidence_parts.append(f"{test_name} {student_score_float} meets minimum {req_score_float}")
                    else:
                        evidence_parts.append(f"{test_name} {student_score_float} below minimum {req_score_float}")
                else:
                    evidence_parts.append(f"Student {test_name} unknown; program requires {req_score_float}")
            except (TypeError, ValueError):
                pass

    if total_checks == 0:
        return 0.70, "No quantifiable requirements to evaluate"

    score = passed_checks / total_checks
    evidence = "; ".join(evidence_parts) if evidence_parts else "Requirements evaluated"

    return score, evidence


def _score_deadline_viability(program: dict[str, Any]) -> tuple[float, str]:
    """Score based on deadline proximity (further deadline = higher score)."""
    deadline = program.get("deadline")

    if deadline is None:
        return 0.70, "No application deadline specified"

    if isinstance(deadline, str):
        try:
            deadline = date.fromisoformat(deadline)
        except ValueError:
            return 0.70, f"Invalid deadline format: {deadline}"

    today = date.today()

    if deadline < today:
        return 0.0, f"Deadline {deadline} has passed"

    days_until = (deadline - today).days

    if days_until >= 180:
        return 1.0, f"Ample time: {days_until} days until deadline ({deadline})"
    if days_until >= 90:
        return 0.85, f"Good time: {days_until} days until deadline ({deadline})"
    if days_until >= 60:
        return 0.70, f"Adequate time: {days_until} days until deadline ({deadline})"
    if days_until >= 30:
        return 0.55, f"Limited time: {days_until} days until deadline ({deadline})"
    if days_until >= 14:
        return 0.40, f"Tight deadline: {days_until} days remaining ({deadline})"

    return 0.25, f"Very tight: only {days_until} days until deadline ({deadline})"


def _score_university_tier(program: dict[str, Any]) -> tuple[float, str]:
    """Score based on university ranking."""
    rank = program.get("institution_rank")

    if rank is None:
        return 0.50, "University ranking not available"

    try:
        rank = int(rank)
    except (TypeError, ValueError):
        return 0.50, f"Invalid ranking format: {rank}"

    if rank <= 0:
        return 0.50, "Invalid ranking value"

    institution_name = program.get("institution_name", "University")

    if rank == 1:
        return 1.0, f"{institution_name} is ranked #1 globally"
    if rank <= 10:
        return 0.95 + (10 - rank) * 0.005, f"{institution_name} is in top 10 (#{rank})"
    if rank <= 25:
        return 0.90 + (25 - rank) * 0.003, f"{institution_name} is in top 25 (#{rank})"
    if rank <= 50:
        return 0.85 + (50 - rank) * 0.002, f"{institution_name} is in top 50 (#{rank})"
    if rank <= 100:
        return 0.75 + (100 - rank) * 0.002, f"{institution_name} is in top 100 (#{rank})"
    if rank <= 200:
        return 0.65 + (200 - rank) * 0.001, f"{institution_name} is in top 200 (#{rank})"
    if rank <= 500:
        return 0.50 + (500 - rank) * 0.0005, f"{institution_name} is in top 500 (#{rank})"
    if rank <= 1000:
        return 0.35 + (1000 - rank) * 0.0003, f"{institution_name} is ranked #{rank}"

    return max(0.20, 0.35 - (rank - 1000) * 0.0001), f"{institution_name} is ranked #{rank}"


def _score_tuition_affordability(
    program: dict[str, Any],
    student_profile: dict[str, Any],
) -> tuple[float, str]:
    """Score based on tuition affordability."""
    tuition = program.get("tuition_usd")
    budget = student_profile.get("max_tuition_usd") or student_profile.get("budget_usd")

    if tuition is None:
        return 0.60, "Tuition information not available"

    try:
        tuition_float = float(tuition)
    except (TypeError, ValueError):
        return 0.60, f"Invalid tuition format: {tuition}"

    if budget is None:
        if tuition_float <= 20000:
            return 0.85, f"Tuition ${tuition_float:,.0f}/year is relatively affordable"
        if tuition_float <= 40000:
            return 0.70, f"Tuition ${tuition_float:,.0f}/year is moderate"
        if tuition_float <= 60000:
            return 0.55, f"Tuition ${tuition_float:,.0f}/year is substantial"
        return 0.40, f"Tuition ${tuition_float:,.0f}/year is high"

    try:
        budget_float = float(budget)
    except (TypeError, ValueError):
        return 0.60, "Invalid budget format in student profile"

    if tuition_float <= budget_float * 0.5:
        return 1.0, f"Tuition ${tuition_float:,.0f} is well under budget ${budget_float:,.0f} (50%)"
    if tuition_float <= budget_float * 0.75:
        return 0.90, f"Tuition ${tuition_float:,.0f} is comfortably within budget ${budget_float:,.0f}"
    if tuition_float <= budget_float:
        return 0.80, f"Tuition ${tuition_float:,.0f} is at budget limit ${budget_float:,.0f}"
    if tuition_float <= budget_float * 1.15:
        return 0.60, f"Tuition ${tuition_float:,.0f} slightly exceeds budget ${budget_float:,.0f}"
    if tuition_float <= budget_float * 1.3:
        return 0.40, f"Tuition ${tuition_float:,.0f} moderately exceeds budget ${budget_float:,.0f}"

    return 0.20, f"Tuition ${tuition_float:,.0f} significantly exceeds budget ${budget_float:,.0f}"


def _calculate_composite_score(
    scores: ProgramMatchScores,
    weights: dict[str, float],
) -> float:
    """Calculate weighted composite score."""
    total = (
        scores.field_relevance * weights.get("field_relevance", 0.35)
        + scores.academic_fit * weights.get("academic_fit", 0.30)
        + scores.deadline_viability * weights.get("deadline_viability", 0.10)
        + scores.university_tier * weights.get("university_tier", 0.15)
        + scores.tuition_affordability * weights.get("tuition_affordability", 0.10)
    )
    return round(total, 3)


def _determine_decision(
    scores: ProgramMatchScores,
    evidence: ProgramEvidence,
    composite_score: float,
    recommend_threshold: float,
    consider_threshold: float,
) -> tuple[ProgramDecision, list[str]]:
    """Determine the decision and generate reason strings."""
    reasons: list[str] = []

    reasons.append(f"field_relevance: {scores.field_relevance:.2f} — {evidence.field_relevance}")
    reasons.append(f"academic_fit: {scores.academic_fit:.2f} — {evidence.academic_fit}")
    reasons.append(f"deadline_viability: {scores.deadline_viability:.2f} — {evidence.deadline_viability}")
    reasons.append(f"university_tier: {scores.university_tier:.2f} — {evidence.university_tier}")
    reasons.append(f"tuition_affordability: {scores.tuition_affordability:.2f} — {evidence.tuition_affordability}")

    if scores.deadline_viability == 0.0:
        return ProgramDecision.FILTER_OUT, reasons

    if composite_score >= recommend_threshold:
        return ProgramDecision.RECOMMEND, reasons
    if composite_score >= consider_threshold:
        return ProgramDecision.CONSIDER, reasons

    return ProgramDecision.FILTER_OUT, reasons


def _build_filters_applied_summary(
    total_programs: int,
    total_filtered: int,
    student_profile: dict[str, Any],
    recommend_threshold: float,
) -> list[str]:
    """Build human-readable summary of filters applied."""
    filters = []

    if student_profile.get("gpa"):
        filters.append(f"Student GPA: {student_profile['gpa']}")

    if student_profile.get("field_of_interest"):
        filters.append(f"Target field: {student_profile['field_of_interest']}")

    if student_profile.get("max_tuition_usd"):
        filters.append(f"Budget limit: ${student_profile['max_tuition_usd']:,.0f}")

    filters.append(f"Composite score threshold: >= {recommend_threshold:.2f} for recommendation")
    filters.append(f"Total evaluated: {total_programs}, filtered out: {total_filtered}")

    return filters


def build_agent_reasoning(
    react_result: dict[str, Any],
    student_profile: dict[str, Any],
    model: str,
    provider: str,
) -> dict[str, Any]:
    """Build the agent_reasoning structure from ReAct results.

    This creates a comprehensive reasoning structure matching the
    Student Profile Agent format for consistency across agents.

    Args:
        react_result: Output from apply_react_ranking_pattern.
        student_profile: The student profile used for ranking.
        model: LLM model name used.
        provider: LLM provider name.

    Returns:
        Complete agent_reasoning dictionary.
    """
    summary = react_result.get("summary", {})
    ranked_programs = react_result.get("ranked_programs", [])
    filters_applied = react_result.get("filters_applied", [])

    profile_summary = _summarize_student_profile(student_profile)

    threshold = summary.get("recommend_threshold", 0.70)
    decision_factors = [
        f"Student profile: {profile_summary}",
        f"Evaluated {summary.get('total_programs_evaluated', 0)} programs",
        f"Recommended {summary.get('total_recommended', 0)} programs (score >= {threshold:.2f})",
        f"Marked {summary.get('total_considered', 0)} programs for consideration",
        f"Filtered out {summary.get('total_filtered_out', 0)} programs (deadline passed or low score)",
    ]

    if ranked_programs:
        top_score = ranked_programs[0].get("composite_score", 0)
        decision_factors.append(f"Top program composite score: {top_score:.2f}")

    weights = summary.get("weights_used", DEFAULT_WEIGHTS)
    approach = (
        f"Applied multi-dimensional scoring with weights: "
        f"field_relevance={weights.get('field_relevance', 0.35):.0%}, "
        f"academic_fit={weights.get('academic_fit', 0.30):.0%}, "
        f"deadline_viability={weights.get('deadline_viability', 0.10):.0%}, "
        f"university_tier={weights.get('university_tier', 0.15):.0%}, "
        f"tuition_affordability={weights.get('tuition_affordability', 0.10):.0%}. "
        f"Programs scored >= {summary.get('recommend_threshold', 0.70):.2f} are recommended."
    )

    ranking_breakdown = []
    for prog in ranked_programs[:10]:
        ranking_breakdown.append(
            {
                "program_id": prog.get("program_id"),
                "program_name": prog.get("program_name"),
                "university": prog.get("university"),
                "country": prog.get("country"),
                "composite_score": prog.get("composite_score"),
                "rank": prog.get("rank"),
                "decision": prog.get("decision"),
                "match_scores": prog.get("match_scores"),
                "evidence": prog.get("evidence"),
            }
        )

    overall_confidence = _calculate_overall_confidence(react_result)

    return {
        "approach": approach,
        "decision_factors": decision_factors,
        "ranking_breakdown": ranking_breakdown,
        "filters_applied": filters_applied,
        "total_programs_evaluated": summary.get("total_programs_evaluated", 0),
        "total_programs_recommended": summary.get("total_recommended", 0),
        "confidence": overall_confidence,
        "model": model,
        "provider": provider,
        "react_decision_trace": react_result.get("react_decision_trace", {}),
    }


def _summarize_student_profile(profile: dict[str, Any]) -> str:
    """Create a concise summary of the student profile."""
    parts = []

    if profile.get("target_degree_level"):
        parts.append(f"{profile['target_degree_level']}'s")
    elif profile.get("degree_seeking"):
        parts.append(f"{profile['degree_seeking']}")

    if profile.get("field_of_interest"):
        parts.append(f"in {profile['field_of_interest']}")

    if profile.get("gpa"):
        parts.append(f"GPA {profile['gpa']}")

    if profile.get("max_tuition_usd"):
        parts.append(f"budget ${profile['max_tuition_usd']:,.0f}")

    return ", ".join(parts) if parts else "Profile details not specified"


def _calculate_overall_confidence(react_result: dict[str, Any]) -> float:
    """Calculate overall confidence in the recommendations."""
    ranked_programs = react_result.get("ranked_programs", [])

    if not ranked_programs:
        return 0.30

    recommended = [p for p in ranked_programs if p.get("decision") == "recommend"]

    if not recommended:
        return 0.50

    avg_score = sum(p.get("composite_score", 0) for p in recommended) / len(recommended)

    coverage_factor = min(len(recommended) / 5, 1.0)

    confidence = avg_score * 0.7 + coverage_factor * 0.3

    return round(min(confidence, 0.99), 2)
