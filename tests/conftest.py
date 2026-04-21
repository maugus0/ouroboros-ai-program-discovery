"""Shared pytest fixtures for Program Discovery Agent tests."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from app.models import (
    DegreeType,
    InstitutionDB,
    InstitutionFocus,
    InstitutionRankingDB,
    InstitutionSize,
    InstitutionStatus,
    InstitutionType,
    ProgramDB,
    ProgramMode,
    ProgramResponse,
    RankingSource,
    ResearchOutput,
)


@pytest.fixture
def sample_institution() -> InstitutionDB:
    """Create a sample institution for testing."""
    return InstitutionDB(
        id="inst-001",
        name="Massachusetts Institute of Technology (MIT)",
        slug="massachusetts-institute-of-technology-mit-united-states",
        country="United States",
        city="Cambridge",
        region="Massachusetts",
        website_url="https://www.mit.edu",
        logo_url=None,
        institution_type=InstitutionType.PRIVATE,
        size=InstitutionSize.LARGE,
        focus=InstitutionFocus.FULL_COMPREHENSIVE,
        research_output=ResearchOutput.VERY_HIGH,
        status=InstitutionStatus.VERIFIED,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_ranking() -> InstitutionRankingDB:
    """Create a sample ranking for testing."""
    return InstitutionRankingDB(
        id="rank-001",
        institution_id="inst-001",
        ranking_source=RankingSource.QS_WORLD,
        ranking_year=2026,
        rank_display="1",
        rank_position=1,
        previous_rank_display="1",
        overall_score=Decimal("100.0"),
        source_url="https://www.topuniversities.com",
        raw_metadata={"academic_reputation": 100.0},
        crawled_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_program() -> ProgramDB:
    """Create a sample program for testing."""
    return ProgramDB(
        id="prog-001",
        institution_id="inst-001",
        program_name="Master of Science in Computer Science",
        degree_type=DegreeType.MASTERS,
        field="Computer Science",
        field_category="Engineering & Technology",
        description="A comprehensive graduate program in computer science.",
        requirements={"gpa": "3.5", "toefl": "100"},
        deadline=date(2026, 12, 15),
        tuition_usd=Decimal("58000"),
        tuition_currency="USD",
        tuition_local=None,
        duration_months=24,
        language="English",
        mode=ProgramMode.ON_CAMPUS,
        intake="Fall",
        source_url="https://www.eecs.mit.edu",
        crawled_at=datetime.utcnow(),
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_program_response(sample_program: ProgramDB) -> ProgramResponse:
    """Create a sample program response with institution details."""
    return ProgramResponse(
        **sample_program.model_dump(),
        institution_name="Massachusetts Institute of Technology (MIT)",
        institution_country="United States",
        institution_rank=1,
    )


@pytest.fixture
def sample_student_profile() -> dict:
    """Create a sample student profile for testing."""
    return {
        "gpa": 3.8,
        "toefl": 110,
        "gre": 325,
        "field_of_interest": "Computer Science",
        "degree_seeking": "Masters",
        "work_experience_years": 2,
    }
