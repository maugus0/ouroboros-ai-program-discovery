"""Tests for application configuration."""

# pylint: disable=import-outside-toplevel
# Imports of ``settings`` are inside tests so each test can set env before load.

import os


def test_settings_load():
    os.environ.setdefault("ALLOW_DB_FAILURE", "true")
    os.environ.setdefault("X_SERVICE_TOKEN", "test-service-token")

    from app.config import settings

    assert settings.DB_NAME == "ouroboros_program_db"
    assert settings.DB_PORT == 3306
    assert settings.DB_POOL_NAME == "program_discovery_pool"


def test_settings_db_helpers():
    os.environ.setdefault("ALLOW_DB_FAILURE", "true")
    os.environ.setdefault("X_SERVICE_TOKEN", "test-service-token")

    from app.config import settings

    assert isinstance(settings.get_db_host(), str)
    assert isinstance(settings.get_db_port(), int)
    assert isinstance(settings.get_db_name(), str)
    assert isinstance(settings.get_db_user(), str)


def test_ranking_weights():
    from app.config import settings

    weights = settings.get_ranking_weights()
    assert isinstance(weights, dict)
    assert sum(weights.values()) == 100
    assert "field_relevance" in weights
    assert "requirement_match" in weights


def test_crawl_settings():
    from app.config import settings

    assert settings.SCRAPY_DOWNLOAD_DELAY >= 1.0
    assert settings.PROGRAM_STALENESS_DAYS > 0
    assert settings.RESPECT_ROBOTS_TXT is True
