"""Pytest configuration and shared fixtures."""

import os

import pytest

os.environ.setdefault("ALLOW_DB_FAILURE", "true")
os.environ.setdefault("USE_MOCK_DATA", "true")
os.environ.setdefault("X_SERVICE_TOKEN", "test-service-token")

from app.config import settings  # noqa: E402  # pylint: disable=wrong-import-position
from app.models.program import StudentProfileSummary  # noqa: E402  # pylint: disable=wrong-import-position


@pytest.fixture
def mock_settings():
    return {
        "DB_HOST": "localhost",
        "DB_NAME": "test_db",
        "USE_MOCK_DATA": True,
        "ALLOW_DB_FAILURE": True,
        "X_SERVICE_TOKEN": settings.X_SERVICE_TOKEN,
    }


@pytest.fixture
def service_token_header():
    """Header value always matches ``settings.X_SERVICE_TOKEN`` (local + CI)."""
    return {"X-Service-Token": settings.X_SERVICE_TOKEN}


@pytest.fixture
def sample_program():
    """A sample program dict for testing."""
    return {
        "id": "test-program-001",
        "university_id": "test-uni-001",
        "university_name": "MIT",
        "program_name": "MSc Computer Science",
        "degree_type": "master_research",
        "field": "Computer Science",
        "field_category": "STEM",
        "description": "A rigorous master's program in CS with a focus on AI and systems.",
        "requirements": {"min_gpa": 3.5, "prerequisites": ["Calculus", "Linear Algebra", "Data Structures"]},
        "deadline": "2026-12-15",
        "tuition_usd": 55000.00,
        "duration_years": 2.0,
        "ranking_score": 95.0,
        "source_url": "https://www.mit.edu/cs/ms",
        "country": "United States",
        "university_ranking": 1,
        "crawled_at": "2026-03-15T10:00:00",
        "is_active": True,
    }


@pytest.fixture
def sample_student_profile():
    """A sample student profile for ranking tests."""
    return StudentProfileSummary(
        gpa=3.8,
        gpa_scale=4.0,
        prerequisites=["Calculus", "Linear Algebra", "Data Structures", "Algorithms"],
        research_interests="machine learning, artificial intelligence",
        target_field="Computer Science",
        budget_usd=60000.0,
    )
