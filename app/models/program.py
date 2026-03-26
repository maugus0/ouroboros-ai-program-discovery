"""Pydantic models for program search requests and responses."""

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class DegreeType(str, Enum):
    BACHELOR = "bachelor"
    MASTER_COURSEWORK = "master_coursework"
    MASTER_RESEARCH = "master_research"
    PHD = "phd"


class StudentProfileSummary(BaseModel):
    """Minimal student profile data needed for program ranking."""

    gpa: Optional[float] = None
    gpa_scale: Optional[float] = Field(default=4.0)
    prerequisites: list[str] = Field(default_factory=list)
    research_interests: Optional[str] = None
    target_field: Optional[str] = None
    budget_usd: Optional[float] = None


class ProgramSearchRequest(BaseModel):
    """Request body for POST /api/v1/programs/search."""

    field: Optional[str] = None
    degree_type: Optional[DegreeType] = None
    country: Optional[str] = None
    student_profile: Optional[StudentProfileSummary] = None
    max_results: int = Field(default=20, ge=1, le=100)
    page: int = Field(default=1, ge=1)


class ProgramResponse(BaseModel):
    """Single program in search results."""

    id: str
    university_name: str
    program_name: str
    degree_type: str
    field: str
    field_category: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[dict[str, Any]] = None
    deadline: Optional[date] = None
    tuition_usd: Optional[float] = None
    duration_years: Optional[float] = None
    ranking_score: Optional[float] = None
    source_url: str
    country: Optional[str] = None
    university_ranking: Optional[int] = None
    crawled_at: Optional[datetime] = None
    match_score: Optional[float] = Field(default=None, description="Weighted match score (0-100)")


class ProgramSearchResponse(BaseModel):
    """Response body for program search."""

    success: bool = True
    data: list[ProgramResponse] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class ProgramDetailResponse(BaseModel):
    """Full program details including requirements."""

    success: bool = True
    data: Optional[ProgramResponse] = None
    requirements: list[dict[str, Any]] = Field(default_factory=list)
