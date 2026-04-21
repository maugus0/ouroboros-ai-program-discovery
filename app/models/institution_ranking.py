"""Pydantic models for institution rankings."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import RankingSource


class InstitutionRankingBase(BaseModel):
    """Base ranking fields."""

    ranking_source: RankingSource
    ranking_year: int = Field(..., ge=1900, le=2100)
    rank_display: str = Field(..., max_length=32)
    rank_position: int = Field(..., ge=1)
    previous_rank_display: str | None = Field(None, max_length=32)
    overall_score: Decimal | None = Field(None, ge=0, le=100)
    source_url: str | None = Field(None, max_length=512)
    raw_metadata: dict[str, Any] | None = None


class InstitutionRankingCreate(InstitutionRankingBase):
    """Request model for creating a ranking entry."""

    institution_id: str


class InstitutionRankingDB(InstitutionRankingBase):
    """Ranking entry as stored in the database."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    crawled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class InstitutionRankingResponse(InstitutionRankingDB):
    """Ranking response with optional institution details."""

    institution_name: str | None = None
    institution_country: str | None = None


class RankingUpsertData(BaseModel):
    """Data for upserting a ranking from crawled/seeded data."""

    institution_id: str
    ranking_source: RankingSource
    ranking_year: int
    rank_display: str
    rank_position: int
    previous_rank_display: str | None = None
    overall_score: Decimal | None = None
    source_url: str | None = None
    raw_metadata: dict[str, Any] | None = None


class QSRankingIndicators(BaseModel):
    """QS-specific ranking indicators stored in raw_metadata."""

    academic_reputation: Decimal | None = None
    employer_reputation: Decimal | None = None
    faculty_student_ratio: Decimal | None = None
    citations_per_faculty: Decimal | None = None
    international_faculty_ratio: Decimal | None = None
    international_students_ratio: Decimal | None = None
    international_research_network: Decimal | None = None
    employment_outcomes: Decimal | None = None
    sustainability: Decimal | None = None
