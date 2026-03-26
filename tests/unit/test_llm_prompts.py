"""Tests for LLM prompt building functions."""

import pytest

from app.llm.prompts import (
    get_field_classification_prompt,
    get_program_extraction_prompt,
    get_requirement_parsing_prompt,
)


def test_program_extraction_prompt_json():
    result = get_program_extraction_prompt(fmt="json")
    assert isinstance(result, str)
    assert "Program Discovery Agent" in result


def test_program_extraction_prompt_text():
    result = get_program_extraction_prompt(fmt="text")
    assert isinstance(result, str)
    assert "AGENT IDENTITY" in result


def test_requirement_parsing_prompt():
    result = get_requirement_parsing_prompt(fmt="json")
    assert isinstance(result, str)
    assert "Admission Requirement Parser" in result


def test_field_classification_prompt():
    result = get_field_classification_prompt(fmt="json")
    assert isinstance(result, str)
    assert "Academic Field Classifier" in result


def test_invalid_format_raises():
    with pytest.raises(ValueError, match="Unsupported prompt format"):
        get_program_extraction_prompt(fmt="xml")


def test_prompt_with_context():
    context = {"source_url": "https://mit.edu/cs", "text_length": 3000}
    result = get_program_extraction_prompt(context=context, fmt="json")
    assert "source_url" in result
