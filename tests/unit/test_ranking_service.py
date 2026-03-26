"""Tests for the weighted ranking service."""

# Exercises small scoring helpers that are intentionally private.

# pylint: disable=protected-access

from app.models.program import StudentProfileSummary
from app.services.ranking_service import RankingService


def test_ranking_with_profile(sample_program, sample_student_profile):
    """Programs should receive a score when a student profile is provided."""
    service = RankingService()
    ranked = service.rank_programs([sample_program], sample_student_profile)

    assert len(ranked) == 1
    assert "match_score" in ranked[0]
    assert ranked[0]["match_score"] > 0


def test_ranking_without_profile(sample_program):
    """Programs should still be scored (with defaults) without a profile."""
    service = RankingService()
    ranked = service.rank_programs([sample_program], None)

    assert len(ranked) == 1
    assert "match_score" in ranked[0]
    assert ranked[0]["match_score"] >= 0


def test_ranking_sorts_descending():
    """Programs should be sorted by match_score in descending order."""
    service = RankingService()
    programs = [
        {
            "id": "1",
            "program_name": "Low Score Program",
            "field": "Art History",
            "university_ranking": 400,
            "requirements": {},
            "deadline": None,
            "tuition_usd": 80000,
        },
        {
            "id": "2",
            "program_name": "High Score Program",
            "field": "Computer Science",
            "university_ranking": 1,
            "requirements": {},
            "deadline": "2027-06-01",
            "tuition_usd": 10000,
        },
    ]
    profile = StudentProfileSummary(target_field="Computer Science")
    ranked = service.rank_programs(programs, profile)

    assert ranked[0]["id"] == "2"
    assert ranked[0]["match_score"] >= ranked[1]["match_score"]


def test_ranking_custom_weights():
    """Custom weights should influence scoring."""
    weights = {
        "field_relevance": 80,
        "requirement_match": 5,
        "university_ranking": 5,
        "deadline_proximity": 5,
        "tuition_affordability": 5,
    }
    service = RankingService(weights=weights)
    programs = [
        {"id": "1", "program_name": "CS PhD", "field": "Computer Science", "university_ranking": 100},
    ]
    profile = StudentProfileSummary(target_field="Computer Science")
    ranked = service.rank_programs(programs, profile)

    assert ranked[0]["match_score"] > 0


def test_university_ranking_score():
    """Top-ranked universities should score higher."""
    service = RankingService()
    top_score = service._score_university_ranking({"university_ranking": 1})
    low_score = service._score_university_ranking({"university_ranking": 400})
    none_score = service._score_university_ranking({"university_ranking": None})

    assert top_score > low_score
    assert none_score == 0.3


def test_deadline_proximity_score():
    """Deadlines further in the future should score higher."""
    service = RankingService()
    far_score = service._score_deadline_proximity({"deadline": "2027-12-31"})
    none_score = service._score_deadline_proximity({"deadline": None})
    past_score = service._score_deadline_proximity({"deadline": "2020-01-01"})

    assert far_score > past_score
    assert none_score == 0.5
    assert past_score == 0.0


def test_tuition_affordability_score():
    """Lower tuition should score higher."""
    service = RankingService()
    cheap_score = service._score_tuition_affordability({"tuition_usd": 5000}, None)
    expensive_score = service._score_tuition_affordability({"tuition_usd": 70000}, None)
    none_score = service._score_tuition_affordability({"tuition_usd": None}, None)

    assert cheap_score > expensive_score
    assert none_score == 0.5


def test_field_relevance_exact_match():
    """Exact field match should score high."""
    service = RankingService()
    profile = StudentProfileSummary(target_field="Computer Science")
    program = {"field": "Computer Science", "program_name": "MSc Computer Science", "description": ""}

    score = service._score_field_relevance(program, profile)
    assert score > 0.5


def test_field_relevance_no_profile():
    """Without a profile, field relevance defaults to 0.5."""
    service = RankingService()
    score = service._score_field_relevance({"field": "CS"}, None)
    assert score == 0.5
