"""Tests for X-Service-Token validation."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_missing_service_token():
    response = client.post("/api/v1/programs/search", json={"field": "CS"})
    assert response.status_code == 401


def test_invalid_service_token():
    response = client.post(
        "/api/v1/programs/search",
        json={"field": "CS"},
        headers={"X-Service-Token": "wrong-token"},
    )
    assert response.status_code == 403


def test_valid_service_token_returns_non_401(service_token_header):
    response = client.post(
        "/api/v1/programs/search",
        json={"field": "CS"},
        headers=service_token_header,
    )
    assert response.status_code not in (401, 403)
