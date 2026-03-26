"""Tests for Pydantic models."""

from app.models.crawl import CrawlRequest, JobType
from app.models.program import DegreeType, ProgramSearchRequest, StudentProfileSummary
from app.models.ranking import RankingBreakdown, RankingWeights


def test_program_search_request_defaults():
    req = ProgramSearchRequest()
    assert req.max_results == 20
    assert req.page == 1
    assert req.field is None
    assert req.degree_type is None


def test_program_search_request_with_values():
    req = ProgramSearchRequest(
        field="Computer Science",
        degree_type=DegreeType.MASTER_RESEARCH,
        max_results=10,
    )
    assert req.field == "Computer Science"
    assert req.degree_type == DegreeType.MASTER_RESEARCH
    assert req.max_results == 10


def test_student_profile_summary():
    profile = StudentProfileSummary(
        gpa=3.8,
        prerequisites=["Calculus", "Linear Algebra"],
        target_field="AI",
    )
    assert profile.gpa == 3.8
    assert len(profile.prerequisites) == 2
    assert profile.gpa_scale == 4.0


def test_crawl_request_on_demand():
    req = CrawlRequest(
        job_type=JobType.ON_DEMAND,
        target_url="https://mit.edu/cs",
    )
    assert req.job_type == JobType.ON_DEMAND
    assert req.target_url == "https://mit.edu/cs"


def test_crawl_request_batch():
    req = CrawlRequest(job_type=JobType.BATCH)
    assert req.job_type == JobType.BATCH
    assert req.target_url is None


def test_ranking_weights():
    weights = RankingWeights()
    total = (
        weights.field_relevance
        + weights.requirement_match
        + weights.university_ranking
        + weights.deadline_proximity
        + weights.tuition_affordability
    )
    assert total == 100


def test_ranking_breakdown():
    breakdown = RankingBreakdown(
        field_relevance_score=80.0,
        requirement_match_score=70.0,
        university_ranking_score=90.0,
        deadline_proximity_score=50.0,
        tuition_affordability_score=60.0,
        total_score=72.5,
    )
    assert breakdown.total_score == 72.5


def test_degree_type_enum():
    assert DegreeType.BACHELOR == "bachelor"
    assert DegreeType.MASTER_RESEARCH == "master_research"
    assert DegreeType.PHD == "phd"
