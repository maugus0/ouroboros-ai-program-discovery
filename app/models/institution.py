"""Pydantic models for institutions."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import (
    InstitutionFocus,
    InstitutionSize,
    InstitutionStatus,
    InstitutionType,
    ResearchOutput,
)


class InstitutionBase(BaseModel):
    """Base institution fields."""

    name: str = Field(..., max_length=512)
    country: str = Field(..., max_length=128)
    city: str | None = Field(None, max_length=128)
    region: str | None = Field(None, max_length=128)
    website_url: str | None = Field(None, max_length=512)
    logo_url: str | None = Field(None, max_length=512)
    institution_type: InstitutionType = InstitutionType.UNKNOWN
    size: InstitutionSize = InstitutionSize.UNKNOWN
    focus: InstitutionFocus = InstitutionFocus.UNKNOWN
    research_output: ResearchOutput = ResearchOutput.UNKNOWN


class InstitutionCreate(InstitutionBase):
    """Request model for creating an institution."""


class InstitutionUpdate(BaseModel):
    """Request model for updating an institution."""

    name: str | None = Field(None, max_length=512)
    country: str | None = Field(None, max_length=128)
    city: str | None = Field(None, max_length=128)
    region: str | None = Field(None, max_length=128)
    website_url: str | None = Field(None, max_length=512)
    logo_url: str | None = Field(None, max_length=512)
    institution_type: InstitutionType | None = None
    size: InstitutionSize | None = None
    focus: InstitutionFocus | None = None
    research_output: ResearchOutput | None = None
    status: InstitutionStatus | None = None
    is_active: bool | None = None


class InstitutionDB(InstitutionBase):
    """Institution as stored in the database."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    status: InstitutionStatus = InstitutionStatus.PENDING
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class InstitutionResponse(InstitutionDB):
    """Institution response with optional ranking data."""

    best_rank: int | None = None
    best_rank_source: str | None = None
    rankings_count: int = 0


class InstitutionSearchRequest(BaseModel):
    """Search/filter request for institutions."""

    query: str | None = Field(None, description="Search by name")
    country: str | None = None
    institution_type: InstitutionType | None = None
    min_rank: int | None = Field(None, ge=1, description="Minimum rank position")
    max_rank: int | None = Field(None, ge=1, description="Maximum rank position")
    ranking_source: str | None = Field(None, description="Filter by ranking source")
    ranking_year: int | None = Field(None, description="Filter by ranking year")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class InstitutionFromRankingData(BaseModel):
    """Model for creating institution from ranking data (e.g., QS seed)."""

    name: str
    country: str
    city: str | None = None
    region: str | None = None
    website_url: str | None = None
    institution_type: InstitutionType = InstitutionType.UNKNOWN
    size: InstitutionSize = InstitutionSize.UNKNOWN
    focus: InstitutionFocus = InstitutionFocus.UNKNOWN
    research_output: ResearchOutput = ResearchOutput.UNKNOWN
