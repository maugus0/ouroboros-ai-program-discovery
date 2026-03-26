"""Tests for Scrapy pipeline validation."""

import pytest
from scrapy.exceptions import DropItem

from app.crawlers.scrapy.pipelines import ValidateProgramPipeline


def test_validate_valid_item():
    pipeline = ValidateProgramPipeline()
    item = {
        "program_name": "MSc Computer Science",
        "source_url": "https://mit.edu/cs/ms",
        "tuition_usd": "55000",
    }
    result = pipeline.process_item(item, spider=None)
    assert result["tuition_usd"] == 55000.0


def test_validate_missing_program_name():
    pipeline = ValidateProgramPipeline()
    item = {"source_url": "https://example.com"}
    with pytest.raises(DropItem, match="program_name"):
        pipeline.process_item(item, spider=None)


def test_validate_missing_source_url():
    pipeline = ValidateProgramPipeline()
    item = {"program_name": "MSc CS"}
    with pytest.raises(DropItem, match="source_url"):
        pipeline.process_item(item, spider=None)


def test_validate_invalid_tuition():
    pipeline = ValidateProgramPipeline()
    item = {
        "program_name": "MSc CS",
        "source_url": "https://example.com",
        "tuition_usd": "not_a_number",
    }
    result = pipeline.process_item(item, spider=None)
    assert result["tuition_usd"] is None


def test_validate_invalid_duration():
    pipeline = ValidateProgramPipeline()
    item = {
        "program_name": "MSc CS",
        "source_url": "https://example.com",
        "duration_years": "two years",
    }
    result = pipeline.process_item(item, spider=None)
    assert result["duration_years"] is None


def test_validate_valid_duration():
    pipeline = ValidateProgramPipeline()
    item = {
        "program_name": "MSc CS",
        "source_url": "https://example.com",
        "duration_years": "1.5",
    }
    result = pipeline.process_item(item, spider=None)
    assert result["duration_years"] == 1.5
