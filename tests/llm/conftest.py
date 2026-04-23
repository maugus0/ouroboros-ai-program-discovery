"""Fixtures for LLM tests."""

from pathlib import Path

import pytest

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


@pytest.fixture
def mock_program_context() -> dict:
    """Provides a realistic mock context for program Q&A prompts."""
    return {
        "question": "What are the best computer science programs?",
        "programs": [
            {
                "program_name": "Master of Computer Science",
                "institution_name": "Stanford University",
                "country": "United States",
                "degree_type": "master",
                "tuition_usd": 55000,
                "deadline": "2026-12-15",
            },
            {
                "program_name": "MSc in Computer Science",
                "institution_name": "MIT",
                "country": "United States",
                "degree_type": "master",
                "tuition_usd": 53000,
                "deadline": "2026-12-01",
            },
        ],
        "student_profile": {
            "gpa": 3.8,
            "field_of_interest": "Artificial Intelligence",
            "target_degree_level": "master",
        },
    }


@pytest.fixture
def mock_institution_context() -> dict:
    """Provides mock institution/university context."""
    return {
        "institutions": [
            {
                "name": "Stanford University",
                "country": "United States",
                "city": "Stanford",
                "rank": 2,
                "overall_score": 98.5,
            },
            {
                "name": "MIT",
                "country": "United States",
                "city": "Cambridge",
                "rank": 1,
                "overall_score": 100.0,
            },
        ]
    }


@pytest.fixture
def mock_student_profile() -> dict:
    """Provides a realistic student profile."""
    return {
        "student_name": "John Doe",
        "gpa": 3.85,
        "gpa_scale": 4.0,
        "nationality": "United States",
        "field_of_study": "Computer Science",
        "degree_type": "master",
        "current_degree_level": "bachelor",
        "target_country": "United States",
    }


@pytest.fixture
def all_prompt_files() -> list[Path]:
    """Returns a list of all prompt JSON files in the prompts directory."""
    if PROMPTS_DIR.exists():
        return list(PROMPTS_DIR.glob("*.json"))
    return []
