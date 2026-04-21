"""Pydantic models for academic programs."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import DegreeType, ProgramMode


class ProgramBase(BaseModel):
    """Base program fields."""

    program_name: str = Field(..., max_length=512)
    degree_type: DegreeType
    field: str = Field(..., max_length=256)
    field_category: str | None = Field(None, max_length=128)
    description: str | None = None
    requirements: dict[str, Any] | None = None
    deadline: date | None = None
    tuition_usd: Decimal | None = Field(None, ge=0)
    tuition_currency: str | None = Field(None, max_length=8)
    tuition_local: Decimal | None = Field(None, ge=0)
    duration_months: int | None = Field(None, ge=1)
    language: str = Field("English", max_length=64)
    mode: ProgramMode = ProgramMode.UNKNOWN
    intake: str | None = Field(None, max_length=64)
    source_url: str | None = Field(None, max_length=512)


class ProgramCreate(ProgramBase):
    """Request model for creating a program."""

    institution_id: str


class ProgramUpdate(BaseModel):
    """Request model for updating a program."""

    program_name: str | None = Field(None, max_length=512)
    degree_type: DegreeType | None = None
    field: str | None = Field(None, max_length=256)
    field_category: str | None = Field(None, max_length=128)
    description: str | None = None
    requirements: dict[str, Any] | None = None
    deadline: date | None = None
    tuition_usd: Decimal | None = None
    tuition_currency: str | None = None
    tuition_local: Decimal | None = None
    duration_months: int | None = None
    language: str | None = None
    mode: ProgramMode | None = None
    intake: str | None = None
    source_url: str | None = None
    is_active: bool | None = None


class ProgramDB(ProgramBase):
    """Program as stored in the database."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    crawled_at: datetime | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class ProgramResponse(ProgramDB):
    """Program response with institution details."""

    institution_name: str | None = None
    institution_country: str | None = None
    institution_rank: int | None = None


class ProgramSearchRequest(BaseModel):
    """Search/filter request for programs."""

    query: str | None = Field(None, description="Search by program name or description")
    institution_id: str | None = None
    degree_type: DegreeType | None = None
    field: str | None = None
    field_category: str | None = None
    country: str | None = None
    min_rank: int | None = Field(None, ge=1)
    max_rank: int | None = Field(None, ge=1)
    max_tuition_usd: Decimal | None = Field(None, ge=0)
    deadline_after: date | None = None
    deadline_before: date | None = None
    language: str | None = None
    mode: ProgramMode | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class ProgramRankingRequest(BaseModel):
    """Request model for ranking programs for a student."""

    student_profile: dict[str, Any] = Field(..., description="Student profile data")
    target_field: str = Field(..., description="Desired field of study")
    target_degree: DegreeType | None = None
    country_preferences: list[str] | None = None
    max_tuition_usd: Decimal | None = None
    deadline_cutoff: date | None = None
    limit: int = Field(20, ge=1, le=100)


class RankedProgram(ProgramResponse):
    """Program with ranking score and breakdown."""

    overall_score: float = Field(..., ge=0, le=100)
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    match_reasons: list[str] = Field(default_factory=list)
