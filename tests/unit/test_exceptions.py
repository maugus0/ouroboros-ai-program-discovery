"""Tests for custom exception hierarchy."""

from app.utils.exceptions import (
    CrawlError,
    DatabaseError,
    LLMExtractionError,
    NotFoundError,
    ProgramDiscoveryBaseError,
    RankingError,
    ServiceAuthError,
    ValidationError,
)


def test_base_error():
    exc = ProgramDiscoveryBaseError("test error", 500)
    assert str(exc) == "test error"
    assert exc.status_code == 500
    assert exc.message == "test error"


def test_not_found_error():
    exc = NotFoundError("Program")
    assert exc.status_code == 404
    assert "Program not found" in exc.message


def test_validation_error():
    exc = ValidationError("Invalid field")
    assert exc.status_code == 422


def test_crawl_error():
    exc = CrawlError("Connection timeout")
    assert exc.status_code == 502


def test_llm_extraction_error():
    exc = LLMExtractionError("OpenAI rate limit")
    assert exc.status_code == 502


def test_ranking_error():
    exc = RankingError()
    assert exc.status_code == 500


def test_service_auth_error():
    exc = ServiceAuthError()
    assert exc.status_code == 401


def test_database_error():
    exc = DatabaseError()
    assert exc.status_code == 500
