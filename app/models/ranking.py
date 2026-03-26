"""Pydantic models for ranking configuration and results."""

from typing import Optional

from pydantic import BaseModel, Field


class RankingWeights(BaseModel):
    """Configurable weights for the program ranking algorithm (must sum to 100)."""

    field_relevance: int = Field(default=40, ge=0, le=100)
    requirement_match: int = Field(default=25, ge=0, le=100)
    university_ranking: int = Field(default=15, ge=0, le=100)
    deadline_proximity: int = Field(default=10, ge=0, le=100)
    tuition_affordability: int = Field(default=10, ge=0, le=100)


class RankingBreakdown(BaseModel):
    """Detailed breakdown of how a program was scored."""

    field_relevance_score: float = 0.0
    requirement_match_score: float = 0.0
    university_ranking_score: float = 0.0
    deadline_proximity_score: float = 0.0
    tuition_affordability_score: float = 0.0
    total_score: float = 0.0


class RankedProgram(BaseModel):
    """A program with its ranking score and breakdown."""

    program_id: str
    program_name: str
    university_name: str
    match_score: float = Field(description="Weighted match score (0-100)")
    breakdown: Optional[RankingBreakdown] = None


class LLMExtractionResult(BaseModel):
    """Result from LLM-based program extraction."""

    extracted_data: dict = Field(default_factory=dict)
    provider: str = ""
    model: str = ""
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
