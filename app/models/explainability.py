"""Pydantic models for explainability and agent reasoning."""

from typing import Any

from pydantic import BaseModel, Field


class ProgramMatchScoresModel(BaseModel):
    """Multi-dimensional match scores for a program."""

    field_relevance: float = Field(ge=0, le=1, description="How well the field matches student interest")
    academic_fit: float = Field(ge=0, le=1, description="How well student meets requirements")
    deadline_viability: float = Field(ge=0, le=1, description="Time remaining until deadline")
    university_tier: float = Field(ge=0, le=1, description="University ranking score")
    tuition_affordability: float = Field(ge=0, le=1, description="How affordable the program is")


class ProgramEvidenceModel(BaseModel):
    """Evidence strings explaining each dimension score."""

    field_relevance: str = Field(description="Evidence for field relevance score")
    academic_fit: str = Field(description="Evidence for academic fit score")
    deadline_viability: str = Field(description="Evidence for deadline viability score")
    university_tier: str = Field(description="Evidence for university tier score")
    tuition_affordability: str = Field(description="Evidence for tuition affordability score")


class ProgramMatchBreakdown(BaseModel):
    """Complete match breakdown for a single program."""

    program_id: str
    program_name: str
    university: str
    country: str | None = None
    composite_score: float = Field(ge=0, le=1)
    rank: int | None = None
    decision: str = Field(description="recommend, consider, or filter_out")
    match_scores: ProgramMatchScoresModel
    evidence: ProgramEvidenceModel


class ProgramDecisionTraceEntry(BaseModel):
    """ReAct decision trace entry for a single program."""

    decision: str = Field(description="recommend, consider, or filter_out")
    reasons: list[str] = Field(default_factory=list)
    composite_score: float = Field(ge=0, le=1)
    rank: int | None = None
    match_scores: dict[str, float] = Field(default_factory=dict)
    evidence: dict[str, str] = Field(default_factory=dict)


class ProgramAgentReasoning(BaseModel):
    """Complete agent reasoning structure for program discovery.

    This model provides full transparency into how programs were
    evaluated and ranked, following the ReAct pattern.
    """

    approach: str = Field(description="High-level description of the ranking approach")
    decision_factors: list[str] = Field(
        default_factory=list,
        description="Key factors that influenced the recommendations",
    )
    ranking_breakdown: list[ProgramMatchBreakdown] = Field(
        default_factory=list,
        description="Top N programs with detailed score breakdown",
    )
    filters_applied: list[str] = Field(
        default_factory=list,
        description="List of filters applied during evaluation",
    )
    total_programs_evaluated: int = Field(ge=0)
    total_programs_recommended: int = Field(ge=0)
    confidence: float = Field(ge=0, le=1, description="Overall confidence in recommendations")
    model: str = Field(description="LLM model used for answer generation")
    provider: str = Field(description="LLM provider (openai or anthropic)")
    react_decision_trace: dict[str, Any] = Field(
        default_factory=dict,
        description="Complete ReAct decision trace for all evaluated programs",
    )


class RankingBreakdownSummary(BaseModel):
    """Summary statistics for the ranking process."""

    total_programs_evaluated: int
    total_recommended: int
    total_considered: int
    total_filtered_out: int
    recommend_threshold: float
    consider_threshold: float
    weights_used: dict[str, float]
