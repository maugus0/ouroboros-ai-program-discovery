"""Unit tests for Pydantic models."""

from decimal import Decimal

from app.models import (
    DegreeType,
    InstitutionCreate,
    InstitutionSearchRequest,
    InstitutionType,
    ProgramCreate,
    ProgramRankingRequest,
    ProgramSearchRequest,
    RankingSource,
)


class TestInstitutionModels:
    """Tests for institution models."""

    def test_institution_create(self):
        """Test creating an institution."""
        data = InstitutionCreate(
            name="Test University",
            country="United States",
            city="New York",
        )
        assert data.name == "Test University"
        assert data.country == "United States"
        assert data.institution_type == InstitutionType.UNKNOWN

    def test_institution_search_request_defaults(self):
        """Test search request default values."""
        request = InstitutionSearchRequest()
        assert request.page == 1
        assert request.page_size == 20
        assert request.query is None

    def test_institution_search_request_with_filters(self):
        """Test search request with filters."""
        request = InstitutionSearchRequest(
            query="MIT",
            country="United States",
            min_rank=1,
            max_rank=100,
            page=2,
            page_size=50,
        )
        assert request.query == "MIT"
        assert request.country == "United States"
        assert request.min_rank == 1
        assert request.max_rank == 100


class TestProgramModels:
    """Tests for program models."""

    def test_program_create(self):
        """Test creating a program."""
        data = ProgramCreate(
            institution_id="inst-001",
            program_name="MSc Computer Science",
            degree_type=DegreeType.MASTERS,
            field="Computer Science",
        )
        assert data.program_name == "MSc Computer Science"
        assert data.degree_type == DegreeType.MASTERS

    def test_program_search_request_defaults(self):
        """Test program search request defaults."""
        request = ProgramSearchRequest()
        assert request.page == 1
        assert request.page_size == 20

    def test_program_ranking_request(self):
        """Test program ranking request."""
        request = ProgramRankingRequest(
            student_profile={"gpa": 3.5},
            target_field="Computer Science",
            target_degree=DegreeType.MASTERS,
            max_tuition_usd=Decimal("60000"),
            limit=10,
        )
        assert request.target_field == "Computer Science"
        assert request.limit == 10


class TestEnums:
    """Tests for enum values."""

    def test_degree_types(self):
        """Test degree type enum values."""
        assert DegreeType.BACHELORS.value == "bachelors"
        assert DegreeType.MASTERS.value == "masters"
        assert DegreeType.PHD.value == "phd"

    def test_ranking_sources(self):
        """Test ranking source enum values."""
        assert RankingSource.QS_WORLD.value == "qs_world"
        assert RankingSource.TIMES_HIGHER.value == "times_higher"

    def test_institution_types(self):
        """Test institution type enum values."""
        assert InstitutionType.PUBLIC.value == "public"
        assert InstitutionType.PRIVATE.value == "private"
