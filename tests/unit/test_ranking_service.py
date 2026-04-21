"""Unit tests for the ranking service."""

from datetime import date
from decimal import Decimal

import pytest

from app.services.ranking_service import RankingService


class TestRankingService:
    """Tests for the ranking service."""

    @pytest.fixture
    def ranking_service(self):
        """Create a ranking service instance."""
        return RankingService()

    def test_normalize_rank_top_1(self, ranking_service):
        """Test rank normalization for #1 ranking."""
        score = ranking_service._normalize_rank(1)
        assert score == 100.0

    def test_normalize_rank_top_10(self, ranking_service):
        """Test rank normalization for top 10."""
        score = ranking_service._normalize_rank(5)
        assert score >= 95.0

    def test_normalize_rank_top_50(self, ranking_service):
        """Test rank normalization for top 50."""
        score = ranking_service._normalize_rank(25)
        assert 85.0 <= score <= 95.0

    def test_normalize_rank_top_100(self, ranking_service):
        """Test rank normalization for top 100."""
        score = ranking_service._normalize_rank(75)
        assert 75.0 <= score <= 85.0

    def test_normalize_rank_top_500(self, ranking_service):
        """Test rank normalization for top 500."""
        score = ranking_service._normalize_rank(300)
        assert 50.0 <= score <= 65.0

    def test_normalize_rank_beyond_1000(self, ranking_service):
        """Test rank normalization for ranks beyond 1000."""
        score = ranking_service._normalize_rank(1500)
        assert score >= 20.0

    def test_score_field_relevance_exact_match(self, ranking_service, sample_program_response):
        """Test field relevance scoring for exact match."""
        score = ranking_service._score_field_relevance(sample_program_response, "Computer Science")
        assert score == 100.0

    def test_score_field_relevance_partial_match(self, ranking_service, sample_program_response):
        """Test field relevance scoring for partial match."""
        score = ranking_service._score_field_relevance(sample_program_response, "Computer")
        assert score >= 70.0

    def test_score_field_relevance_no_match(self, ranking_service, sample_program_response):
        """Test field relevance scoring for no match."""
        score = ranking_service._score_field_relevance(sample_program_response, "Biology")
        assert score <= 50.0

    def test_score_requirement_match_all_met(self, ranking_service, sample_program_response):
        """Test requirement matching when all requirements are met."""
        student = {"gpa": 4.0, "toefl": 120}
        score = ranking_service._score_requirement_match(sample_program_response, student)
        assert score == 100.0

    def test_score_requirement_match_partial(self, ranking_service, sample_program_response):
        """Test requirement matching when some requirements are met."""
        student = {"gpa": 4.0, "toefl": 80}
        score = ranking_service._score_requirement_match(sample_program_response, student)
        assert 40.0 <= score <= 60.0

    def test_score_deadline_proximity_far_future(self, ranking_service):
        """Test deadline scoring for deadlines far in the future."""
        future_date = date.today().replace(year=date.today().year + 1)
        score = ranking_service._score_deadline_proximity(future_date)
        assert score == 100.0

    def test_score_deadline_proximity_past(self, ranking_service):
        """Test deadline scoring for past deadlines."""
        past_date = date(2020, 1, 1)
        score = ranking_service._score_deadline_proximity(past_date)
        assert score == 0.0

    def test_score_deadline_proximity_none(self, ranking_service):
        """Test deadline scoring when deadline is None."""
        score = ranking_service._score_deadline_proximity(None)
        assert score == 70.0

    def test_score_tuition_affordability_within_budget(self, ranking_service):
        """Test tuition scoring when tuition is within budget."""
        score = ranking_service._score_tuition_affordability(Decimal("30000"), Decimal("60000"))
        assert score >= 90.0

    def test_score_tuition_affordability_at_budget(self, ranking_service):
        """Test tuition scoring when tuition equals budget."""
        score = ranking_service._score_tuition_affordability(Decimal("60000"), Decimal("60000"))
        assert score == 80.0

    def test_score_tuition_affordability_over_budget(self, ranking_service):
        """Test tuition scoring when tuition exceeds budget."""
        score = ranking_service._score_tuition_affordability(Decimal("80000"), Decimal("60000"))
        assert score <= 50.0

    def test_score_university_ranking_none(self, ranking_service):
        """Test university ranking scoring when rank is None."""
        score = ranking_service._score_university_ranking(None)
        assert score == 50.0

    def test_score_university_ranking_top_10(self, ranking_service):
        """Test university ranking scoring for top 10."""
        score = ranking_service._score_university_ranking(5)
        assert score >= 95.0
