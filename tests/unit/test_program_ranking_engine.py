"""Unit tests for the ReAct program ranking engine."""

from datetime import date, timedelta

import pytest

from app.agents.program_discovery.program_ranking_engine import (
    DEFAULT_WEIGHTS,
    ProgramDecision,
    ProgramMatchScores,
    _calculate_composite_score,
    _determine_decision,
    _score_academic_fit,
    _score_deadline_viability,
    _score_field_relevance,
    _score_tuition_affordability,
    _score_university_tier,
    apply_react_ranking_pattern,
    build_agent_reasoning,
)


class TestFieldRelevanceScoring:
    """Tests for field relevance scoring."""

    def test_exact_match_scores_perfect(self):
        """Exact field match should score 1.0."""
        program = {"field": "Computer Science", "field_category": "Engineering"}
        profile = {"field_of_interest": "Computer Science"}

        score, evidence = _score_field_relevance(program, profile)

        assert score == 1.0
        assert "Perfect match" in evidence

    def test_partial_match_scores_high(self):
        """Partial field match should score high."""
        program = {"field": "Computer Science and Engineering", "field_category": "Engineering"}
        profile = {"field_of_interest": "Computer Science"}

        score, evidence = _score_field_relevance(program, profile)

        assert score >= 0.85
        assert "align" in evidence.lower() or "match" in evidence.lower()

    def test_word_overlap_scores_moderately(self):
        """Word overlap should score moderately."""
        program = {"field": "Data Science", "field_category": "Technology"}
        profile = {"field_of_interest": "Computer Science"}

        score, evidence = _score_field_relevance(program, profile)

        assert 0.6 <= score <= 0.8
        assert "overlap" in evidence.lower() or "common" in evidence.lower()

    def test_no_match_scores_low(self):
        """No field match should score low."""
        program = {"field": "Biology", "field_category": "Life Sciences"}
        profile = {"field_of_interest": "Computer Science"}

        score, evidence = _score_field_relevance(program, profile)

        assert score <= 0.4
        assert "Limited" in evidence or "differs" in evidence.lower()

    def test_missing_profile_field_returns_default(self):
        """Missing student field should return default score."""
        program = {"field": "Computer Science"}
        profile = {}

        score, evidence = _score_field_relevance(program, profile)

        assert score == 0.70
        assert "No target field" in evidence

    def test_category_match_when_no_direct_match(self):
        """Category match should score moderately."""
        program = {"field": "Artificial Intelligence", "field_category": "Computer Science"}
        profile = {"field_of_interest": "computer science"}

        score, _ = _score_field_relevance(program, profile)

        assert score >= 0.60


class TestAcademicFitScoring:
    """Tests for academic fit scoring."""

    def test_all_requirements_met_scores_perfect(self):
        """Meeting all requirements should score 1.0."""
        program = {"requirements": {"gpa": 3.5, "toefl": 100}}
        profile = {"gpa": 3.8, "toefl": 110}

        score, evidence = _score_academic_fit(program, profile)

        assert score == 1.0
        assert "GPA" in evidence
        assert "TOEFL" in evidence

    def test_partial_requirements_met(self):
        """Meeting some requirements should score proportionally."""
        program = {"requirements": {"gpa": 3.5, "toefl": 100}}
        profile = {"gpa": 3.8, "toefl": 90}

        score, evidence = _score_academic_fit(program, profile)

        assert 0.4 <= score <= 0.6
        assert "meets" in evidence.lower() or "exceeds" in evidence.lower()
        assert "below" in evidence.lower()

    def test_no_requirements_returns_default(self):
        """No requirements should return default score."""
        program = {"requirements": {}}
        profile = {"gpa": 3.8}

        score, evidence = _score_academic_fit(program, profile)

        assert score == 0.70
        assert "No" in evidence

    def test_gpa_exceeds_by_margin_noted(self):
        """GPA exceeding by margin should be noted in evidence."""
        program = {"requirements": {"gpa": 3.0}}
        profile = {"gpa": 3.8}

        score, evidence = _score_academic_fit(program, profile)

        assert score == 1.0
        assert "exceeds" in evidence.lower()


class TestDeadlineViabilityScoring:
    """Tests for deadline viability scoring."""

    def test_far_deadline_scores_perfect(self):
        """Deadline 180+ days away should score 1.0."""
        deadline = date.today() + timedelta(days=200)
        program = {"deadline": deadline}

        score, evidence = _score_deadline_viability(program)

        assert score == 1.0
        assert "Ample time" in evidence

    def test_moderate_deadline_scores_high(self):
        """Deadline 90+ days away should score high."""
        deadline = date.today() + timedelta(days=95)
        program = {"deadline": deadline}

        score, evidence = _score_deadline_viability(program)

        assert score >= 0.80
        assert "Good time" in evidence

    def test_tight_deadline_scores_low(self):
        """Deadline < 30 days should score low."""
        deadline = date.today() + timedelta(days=10)
        program = {"deadline": deadline}

        score, evidence = _score_deadline_viability(program)

        assert score <= 0.30
        assert "tight" in evidence.lower()

    def test_passed_deadline_scores_zero(self):
        """Past deadline should score 0.0."""
        deadline = date.today() - timedelta(days=10)
        program = {"deadline": deadline}

        score, evidence = _score_deadline_viability(program)

        assert score == 0.0
        assert "passed" in evidence.lower()

    def test_no_deadline_returns_default(self):
        """No deadline should return default score."""
        program = {"deadline": None}

        score, evidence = _score_deadline_viability(program)

        assert score == 0.70
        assert "No application deadline" in evidence

    def test_string_deadline_parsed_correctly(self):
        """String deadline should be parsed correctly."""
        deadline_str = (date.today() + timedelta(days=100)).isoformat()
        program = {"deadline": deadline_str}

        score, _ = _score_deadline_viability(program)

        assert score >= 0.80


class TestUniversityTierScoring:
    """Tests for university tier scoring."""

    def test_rank_1_scores_perfect(self):
        """Rank #1 should score 1.0."""
        program = {"institution_rank": 1, "institution_name": "MIT"}

        score, evidence = _score_university_tier(program)

        assert score == 1.0
        assert "#1 globally" in evidence

    def test_top_10_scores_very_high(self):
        """Top 10 should score very high."""
        program = {"institution_rank": 5, "institution_name": "Stanford"}

        score, evidence = _score_university_tier(program)

        assert score >= 0.95
        assert "top 10" in evidence

    def test_top_100_scores_high(self):
        """Top 100 should score high."""
        program = {"institution_rank": 75, "institution_name": "University of Michigan"}

        score, evidence = _score_university_tier(program)

        assert 0.75 <= score <= 0.85
        assert "top 100" in evidence

    def test_no_rank_returns_default(self):
        """No ranking should return default score."""
        program = {"institution_rank": None, "institution_name": "Unknown University"}

        score, evidence = _score_university_tier(program)

        assert score == 0.50
        assert "not available" in evidence


class TestTuitionAffordabilityScoring:
    """Tests for tuition affordability scoring."""

    def test_well_under_budget_scores_perfect(self):
        """Tuition well under budget should score 1.0."""
        program = {"tuition_usd": 25000}
        profile = {"max_tuition_usd": 60000}

        score, evidence = _score_tuition_affordability(program, profile)

        assert score == 1.0
        assert "well under budget" in evidence.lower()

    def test_at_budget_scores_good(self):
        """Tuition at budget should score 0.80."""
        program = {"tuition_usd": 60000}
        profile = {"max_tuition_usd": 60000}

        score, evidence = _score_tuition_affordability(program, profile)

        assert score == 0.80
        assert "at budget limit" in evidence.lower()

    def test_over_budget_scores_low(self):
        """Tuition over budget should score low."""
        program = {"tuition_usd": 80000}
        profile = {"max_tuition_usd": 60000}

        score, evidence = _score_tuition_affordability(program, profile)

        assert score <= 0.50
        assert "exceeds" in evidence.lower()

    def test_no_budget_specified_uses_tiers(self):
        """No budget specified should use tier-based scoring."""
        program = {"tuition_usd": 25000}
        profile = {}

        score, evidence = _score_tuition_affordability(program, profile)

        # $25k falls into "moderate" tier (0.70) when no budget specified
        assert score >= 0.70
        assert "moderate" in evidence.lower() or "affordable" in evidence.lower()


class TestCompositeScoring:
    """Tests for composite score calculation."""

    def test_perfect_scores_yield_perfect_composite(self):
        """All perfect scores should yield 1.0 composite."""
        scores = ProgramMatchScores(
            field_relevance=1.0,
            academic_fit=1.0,
            deadline_viability=1.0,
            university_tier=1.0,
            tuition_affordability=1.0,
        )

        composite = _calculate_composite_score(scores, DEFAULT_WEIGHTS)

        assert composite == 1.0

    def test_weights_are_applied_correctly(self):
        """Custom weights should be applied correctly."""
        scores = ProgramMatchScores(
            field_relevance=1.0,
            academic_fit=0.0,
            deadline_viability=0.0,
            university_tier=0.0,
            tuition_affordability=0.0,
        )

        weights = {
            "field_relevance": 1.0,
            "academic_fit": 0.0,
            "deadline_viability": 0.0,
            "university_tier": 0.0,
            "tuition_affordability": 0.0,
        }

        composite = _calculate_composite_score(scores, weights)

        assert composite == 1.0


class TestDecisionDetermination:
    """Tests for decision determination logic."""

    def test_high_score_recommends(self):
        """High composite score should recommend."""
        scores = ProgramMatchScores(
            field_relevance=0.9,
            academic_fit=0.85,
            deadline_viability=0.80,
            university_tier=0.90,
            tuition_affordability=0.85,
        )
        from app.agents.program_discovery.program_ranking_engine import ProgramEvidence

        evidence = ProgramEvidence()

        decision, reasons = _determine_decision(scores, evidence, 0.85, 0.70, 0.50)

        assert decision == ProgramDecision.RECOMMEND
        assert len(reasons) == 5

    def test_moderate_score_considers(self):
        """Moderate composite score should consider."""
        scores = ProgramMatchScores(
            field_relevance=0.6,
            academic_fit=0.6,
            deadline_viability=0.6,
            university_tier=0.6,
            tuition_affordability=0.6,
        )
        from app.agents.program_discovery.program_ranking_engine import ProgramEvidence

        evidence = ProgramEvidence()

        decision, _ = _determine_decision(scores, evidence, 0.60, 0.70, 0.50)

        assert decision == ProgramDecision.CONSIDER

    def test_passed_deadline_filters_out(self):
        """Zero deadline score should filter out regardless of composite."""
        scores = ProgramMatchScores(
            field_relevance=1.0,
            academic_fit=1.0,
            deadline_viability=0.0,
            university_tier=1.0,
            tuition_affordability=1.0,
        )
        from app.agents.program_discovery.program_ranking_engine import ProgramEvidence

        evidence = ProgramEvidence()

        decision, _ = _determine_decision(scores, evidence, 0.80, 0.70, 0.50)

        assert decision == ProgramDecision.FILTER_OUT


class TestApplyReactRankingPattern:
    """Integration tests for the full ReAct pattern."""

    @pytest.fixture
    def sample_programs(self):
        """Create sample programs for testing."""
        return [
            {
                "id": "prog-001",
                "program_name": "MS Computer Science",
                "institution_name": "MIT",
                "institution_country": "United States",
                "institution_rank": 1,
                "field": "Computer Science",
                "field_category": "Engineering",
                "requirements": {"gpa": 3.5, "toefl": 100},
                "deadline": (date.today() + timedelta(days=120)).isoformat(),
                "tuition_usd": 55000,
            },
            {
                "id": "prog-002",
                "program_name": "MS Data Science",
                "institution_name": "Stanford",
                "institution_country": "United States",
                "institution_rank": 3,
                "field": "Data Science",
                "field_category": "Technology",
                "requirements": {"gpa": 3.3, "gre": 320},
                "deadline": (date.today() + timedelta(days=90)).isoformat(),
                "tuition_usd": 58000,
            },
            {
                "id": "prog-003",
                "program_name": "MS Biology",
                "institution_name": "Harvard",
                "institution_country": "United States",
                "institution_rank": 5,
                "field": "Biology",
                "field_category": "Life Sciences",
                "requirements": {"gpa": 3.4},
                "deadline": (date.today() - timedelta(days=10)).isoformat(),
                "tuition_usd": 52000,
            },
        ]

    @pytest.fixture
    def sample_profile(self):
        """Create a sample student profile."""
        return {
            "field_of_interest": "Computer Science",
            "gpa": 3.8,
            "toefl": 110,
            "gre": 325,
            "max_tuition_usd": 60000,
        }

    def test_returns_expected_structure(self, sample_programs, sample_profile):
        """Result should contain all expected keys."""
        result = apply_react_ranking_pattern(sample_programs, sample_profile)

        assert "react_decision_trace" in result
        assert "ranked_programs" in result
        assert "filters_applied" in result
        assert "summary" in result

    def test_programs_are_ranked_by_composite_score(self, sample_programs, sample_profile):
        """Programs should be sorted by composite score descending."""
        result = apply_react_ranking_pattern(sample_programs, sample_profile)
        ranked = result["ranked_programs"]

        scores = [p["composite_score"] for p in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_passed_deadline_is_filtered_out(self, sample_programs, sample_profile):
        """Program with passed deadline should be filtered out."""
        result = apply_react_ranking_pattern(sample_programs, sample_profile)

        ranked_ids = [p["program_id"] for p in result["ranked_programs"]]
        assert "prog-003" not in ranked_ids

        trace = result["react_decision_trace"]["prog-003"]
        assert trace["decision"] == "filter_out"

    def test_best_match_is_ranked_first(self, sample_programs, sample_profile):
        """Best matching program should be ranked first."""
        result = apply_react_ranking_pattern(sample_programs, sample_profile)
        ranked = result["ranked_programs"]

        assert ranked[0]["program_id"] == "prog-001"
        assert ranked[0]["rank"] == 1

    def test_decision_trace_has_all_programs(self, sample_programs, sample_profile):
        """Decision trace should have entries for all programs."""
        result = apply_react_ranking_pattern(sample_programs, sample_profile)

        assert len(result["react_decision_trace"]) == len(sample_programs)

    def test_match_scores_are_normalized(self, sample_programs, sample_profile):
        """All match scores should be between 0 and 1."""
        result = apply_react_ranking_pattern(sample_programs, sample_profile)

        for prog in result["ranked_programs"]:
            scores = prog["match_scores"]
            for key, value in scores.items():
                assert 0 <= value <= 1, f"{key} score {value} out of range"

    def test_evidence_strings_are_populated(self, sample_programs, sample_profile):
        """Evidence strings should be populated for all dimensions."""
        result = apply_react_ranking_pattern(sample_programs, sample_profile)

        for prog in result["ranked_programs"]:
            evidence = prog["evidence"]
            assert evidence["field_relevance"]
            assert evidence["academic_fit"]
            assert evidence["deadline_viability"]
            assert evidence["university_tier"]
            assert evidence["tuition_affordability"]


class TestBuildAgentReasoning:
    """Tests for agent reasoning builder."""

    @pytest.fixture
    def sample_react_result(self):
        """Create sample ReAct result."""
        return {
            "react_decision_trace": {
                "prog-001": {
                    "decision": "recommend",
                    "reasons": ["High score"],
                    "composite_score": 0.85,
                    "rank": 1,
                    "match_scores": {"field_relevance": 0.9},
                    "evidence": {"field_relevance": "Good match"},
                }
            },
            "ranked_programs": [
                {
                    "program_id": "prog-001",
                    "program_name": "MS CS",
                    "university": "MIT",
                    "country": "USA",
                    "composite_score": 0.85,
                    "rank": 1,
                    "decision": "recommend",
                    "match_scores": {"field_relevance": 0.9},
                    "evidence": {"field_relevance": "Good match"},
                }
            ],
            "filters_applied": ["Student GPA: 3.8"],
            "summary": {
                "total_programs_evaluated": 10,
                "total_recommended": 3,
                "total_considered": 2,
                "total_filtered_out": 5,
                "recommend_threshold": 0.70,
                "consider_threshold": 0.50,
                "weights_used": DEFAULT_WEIGHTS,
            },
        }

    @pytest.fixture
    def sample_profile(self):
        """Create sample student profile."""
        return {
            "field_of_interest": "Computer Science",
            "gpa": 3.8,
            "target_degree_level": "Master",
        }

    def test_returns_expected_structure(self, sample_react_result, sample_profile):
        """Agent reasoning should have all expected fields."""
        reasoning = build_agent_reasoning(
            react_result=sample_react_result,
            student_profile=sample_profile,
            model="gpt-4o-mini",
            provider="openai",
        )

        assert "approach" in reasoning
        assert "decision_factors" in reasoning
        assert "ranking_breakdown" in reasoning
        assert "filters_applied" in reasoning
        assert "total_programs_evaluated" in reasoning
        assert "total_programs_recommended" in reasoning
        assert "confidence" in reasoning
        assert "model" in reasoning
        assert "provider" in reasoning

    def test_approach_describes_weights(self, sample_react_result, sample_profile):
        """Approach should describe the weighting strategy."""
        reasoning = build_agent_reasoning(
            react_result=sample_react_result,
            student_profile=sample_profile,
            model="gpt-4o-mini",
            provider="openai",
        )

        assert "field_relevance" in reasoning["approach"]
        assert "academic_fit" in reasoning["approach"]

    def test_decision_factors_summarize_process(self, sample_react_result, sample_profile):
        """Decision factors should summarize the evaluation process."""
        reasoning = build_agent_reasoning(
            react_result=sample_react_result,
            student_profile=sample_profile,
            model="gpt-4o-mini",
            provider="openai",
        )

        factors = reasoning["decision_factors"]
        assert any("profile" in f.lower() for f in factors)
        assert any("evaluated" in f.lower() for f in factors)
        assert any("recommended" in f.lower() for f in factors)

    def test_confidence_is_calculated(self, sample_react_result, sample_profile):
        """Confidence should be calculated and in valid range."""
        reasoning = build_agent_reasoning(
            react_result=sample_react_result,
            student_profile=sample_profile,
            model="gpt-4o-mini",
            provider="openai",
        )

        assert 0 <= reasoning["confidence"] <= 1
