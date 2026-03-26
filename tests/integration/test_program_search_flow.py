"""Integration tests for the program search flow."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_search_programs_authenticated(service_token_header):
    """Authenticated search should return a response (even if empty from no DB)."""
    response = client.post(
        "/api/v1/programs/search",
        json={"field": "Computer Science", "max_results": 5},
        headers=service_token_header,
    )
    assert response.status_code in (200, 503)


def test_search_programs_with_student_profile(service_token_header):
    """Search with student profile should be accepted."""
    response = client.post(
        "/api/v1/programs/search",
        json={
            "field": "Computer Science",
            "degree_type": "master_research",
            "student_profile": {
                "gpa": 3.8,
                "prerequisites": ["Calculus"],
                "target_field": "Computer Science",
            },
            "max_results": 10,
        },
        headers=service_token_header,
    )
    assert response.status_code in (200, 503)


def test_get_program_not_found(service_token_header):
    """Getting a non-existent program should return 404 or 503 (no DB)."""
    response = client.get(
        "/api/v1/programs/non-existent-id",
        headers=service_token_header,
    )
    assert response.status_code in (404, 503)
