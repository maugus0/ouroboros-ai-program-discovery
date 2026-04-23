"""LLMOps tests for the eval runner contract and deterministic judge behavior.

Tests the evaluation runner's core functions to ensure consistent
behavior across CI runs and proper bias detection.
"""

import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts import run_llm_eval  # noqa: E402  # pylint: disable=C0413


class TestDryRunBiasScores:
    """Tests for dry-run bias score generation."""

    def test_default_scores_produce_passing_gap(self, monkeypatch):
        """Default dry-run scores should not trigger bias warnings."""
        monkeypatch.delenv("EVAL_DRY_RUN_BIAS_SCORES", raising=False)

        score_0 = run_llm_eval.get_dry_run_bias_score(0)
        score_1 = run_llm_eval.get_dry_run_bias_score(1)
        score_2 = run_llm_eval.get_dry_run_bias_score(2)

        assert score_0 == 7.0
        assert score_1 == 7.5
        assert score_2 == 7.5

        gap = max(score_0, score_1, score_2) - min(score_0, score_1, score_2)
        assert gap < 1.5

    def test_custom_scores_from_env_variable(self, monkeypatch):
        """Environment variable should override default bias scores."""
        monkeypatch.setenv("EVAL_DRY_RUN_BIAS_SCORES", "6.0, 9.5")

        assert run_llm_eval.get_dry_run_bias_score(0) == 6.0
        assert run_llm_eval.get_dry_run_bias_score(1) == 9.5
        assert run_llm_eval.get_dry_run_bias_score(2) == 9.5

    def test_single_score_reused_for_all_variants(self, monkeypatch):
        """Single score should be used for all variant indices."""
        monkeypatch.setenv("EVAL_DRY_RUN_BIAS_SCORES", "8.0")

        assert run_llm_eval.get_dry_run_bias_score(0) == 8.0
        assert run_llm_eval.get_dry_run_bias_score(5) == 8.0


class TestBiasGapClassification:
    """Tests for bias gap classification logic."""

    @pytest.mark.parametrize(
        ("bias_gap", "expected_status", "expected_hard_fail"),
        [
            (0.0, "ok", False),
            (0.5, "ok", False),
            (1.4, "ok", False),
            (1.5, "ok", False),
            (1.6, "warning", False),
            (2.0, "warning", False),
            (2.9, "warning", False),
            (3.0, "warning", False),
            (3.1, "hard_fail", True),
            (3.5, "hard_fail", True),
            (5.0, "hard_fail", True),
        ],
    )
    def test_classification_boundaries(
        self,
        bias_gap: float,
        expected_status: str,
        expected_hard_fail: bool,
    ):
        """Verify bias gap classification at boundary values."""
        status, hard_fail = run_llm_eval.classify_bias_gap(
            bias_gap,
            bias_threshold=1.5,
            bias_hard_limit=3.0,
        )

        assert status == expected_status
        assert hard_fail is expected_hard_fail

    def test_custom_thresholds(self):
        """Classification should respect custom thresholds."""
        status, hard_fail = run_llm_eval.classify_bias_gap(
            bias_gap=1.0,
            bias_threshold=0.5,
            bias_hard_limit=2.0,
        )

        assert status == "warning"
        assert hard_fail is False


class TestPromptVersioning:
    """Tests for prompt version computation."""

    def test_version_from_existing_file(self, tmp_path):
        """Version should be computed from file contents."""
        prompts_file = tmp_path / "prompts.py"
        prompts_file.write_text("def get_prompt(): return 'test'")

        version = run_llm_eval.compute_prompt_version(prompts_file)

        assert len(version) == 12
        assert version.isalnum()

    def test_version_unknown_for_missing_file(self, tmp_path):
        """Missing file should return 'unknown' version."""
        missing_file = tmp_path / "nonexistent.py"

        version = run_llm_eval.compute_prompt_version(missing_file)

        assert version == "unknown"

    def test_version_changes_with_content(self, tmp_path):
        """Version should change when file content changes."""
        prompts_file = tmp_path / "prompts.py"

        prompts_file.write_text("version 1")
        version_1 = run_llm_eval.compute_prompt_version(prompts_file)

        prompts_file.write_text("version 2")
        version_2 = run_llm_eval.compute_prompt_version(prompts_file)

        assert version_1 != version_2


@pytest.mark.asyncio
class TestAsyncEvalFunctions:
    """Tests for async evaluation functions."""

    async def test_generate_response_dry_run_returns_mock(self):
        """Dry run should return mock response without calling LLM."""
        result = await run_llm_eval.generate_response(
            context={"question": "test question"},
            dry_run=True,
        )

        assert "content" in result
        assert result["model"] == "gpt-4o-mock"
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 200

    async def test_judge_output_dry_run_returns_mock(self):
        """Dry run judge should return mock score."""
        result = await run_llm_eval.judge_output(
            input_context={"question": "test"},
            output_text="Generated response.",
            rubric="Score 1-10.",
            criteria="Prefer accuracy.",
            dry_run=True,
        )

        assert result["score"] == 7.5
        assert "mock" in result["reason"].lower()
        assert result["model"] == "gpt-4o-mini-mock"
