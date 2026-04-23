"""Tests for structural validity of prompts (Linting).

Validates:
- Prompt functions return non-empty strings
- Prompts don't exceed token budgets
- Prompts render correctly with context
"""

import re

import pytest

from app.llm.prompts import (
    get_eligibility_check_prompt,
    get_program_comparison_prompt,
    get_program_qa_prompt,
)

PLACEHOLDER_PATTERN = re.compile(r"\{\{.*?\}\}")

OPENAI_LIMIT = 128_000
ANTHROPIC_LIMIT = 200_000
MAX_ALLOWED_TOKENS = int(min(OPENAI_LIMIT, ANTHROPIC_LIMIT) * 0.8)


def estimate_token_count(text: str) -> int:
    """Rough token estimation: ~4 chars per token."""
    return len(text) // 4


def assert_no_unrendered_placeholders(rendered_text: str) -> None:
    """Ensures that no `{{ placeholder }}` remains in the string after rendering."""
    matches = PLACEHOLDER_PATTERN.findall(rendered_text)
    assert not matches, f"Found unrendered placeholders in prompt: {matches}"


def assert_token_count_within_limit(rendered_text: str) -> None:
    """Ensures the rendered prompt isn't excessively large."""
    tokens = estimate_token_count(rendered_text)
    assert tokens < MAX_ALLOWED_TOKENS, f"Prompt token count ({tokens}) exceeds safe limit ({MAX_ALLOWED_TOKENS})."


class TestPromptQA:
    """Tests for program Q&A prompt."""

    def test_prompt_returns_string(self):
        """Verify prompt function returns non-empty string."""
        prompt = get_program_qa_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_prompt_contains_key_instructions(self):
        """Verify prompt contains expected instruction elements."""
        prompt = get_program_qa_prompt()
        assert "expert" in prompt.lower() or "advisor" in prompt.lower()
        assert "JSON" in prompt or "json" in prompt

    def test_prompt_within_token_budget(self):
        """Verify prompt doesn't exceed token limits."""
        prompt = get_program_qa_prompt()
        assert_token_count_within_limit(prompt)

    def test_prompt_no_unrendered_placeholders(self):
        """Verify no template placeholders remain."""
        prompt = get_program_qa_prompt()
        assert_no_unrendered_placeholders(prompt)


class TestPromptComparison:
    """Tests for program comparison prompt."""

    def test_prompt_returns_string(self):
        """Verify prompt function returns non-empty string."""
        prompt = get_program_comparison_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_prompt_contains_comparison_instructions(self):
        """Verify prompt mentions comparison-related terms."""
        prompt = get_program_comparison_prompt()
        lower = prompt.lower()
        assert "compare" in lower or "comparison" in lower

    def test_prompt_within_token_budget(self):
        """Verify prompt doesn't exceed token limits."""
        prompt = get_program_comparison_prompt()
        assert_token_count_within_limit(prompt)


class TestPromptEligibility:
    """Tests for eligibility check prompt."""

    def test_prompt_returns_string(self):
        """Verify prompt function returns non-empty string."""
        prompt = get_eligibility_check_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_prompt_contains_eligibility_terms(self):
        """Verify prompt mentions eligibility-related terms."""
        prompt = get_eligibility_check_prompt()
        lower = prompt.lower()
        assert "eligib" in lower

    def test_prompt_within_token_budget(self):
        """Verify prompt doesn't exceed token limits."""
        prompt = get_eligibility_check_prompt()
        assert_token_count_within_limit(prompt)


class TestAllPrompts:
    """Cross-cutting tests for all prompts."""

    @pytest.mark.parametrize(
        "prompt_fn",
        [get_program_qa_prompt, get_program_comparison_prompt, get_eligibility_check_prompt],
    )
    def test_prompts_are_reasonable_length(self, prompt_fn):
        """All prompts should be between 100 and 10000 chars."""
        prompt = prompt_fn()
        assert 100 < len(prompt) < 10000, f"Prompt length {len(prompt)} is outside reasonable bounds"

    @pytest.mark.parametrize(
        "prompt_fn",
        [get_program_qa_prompt, get_program_comparison_prompt, get_eligibility_check_prompt],
    )
    def test_prompts_request_json_format(self, prompt_fn):
        """All prompts should mention JSON output format."""
        prompt = prompt_fn()
        assert "json" in prompt.lower(), "Prompt should specify JSON output format"
