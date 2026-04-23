"""Integration tests for PDA explainability flow.

Note: Tests in TestChatAskWithExplainability require a running database
and are skipped in environments without DB access (pre-commit, CI without DB).
"""

import os
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import DegreeType, ProgramMode, ProgramResponse

# Skip tests requiring full app/DB if ALLOW_DB_FAILURE is set
SKIP_FULL_APP_TESTS = os.getenv("ALLOW_DB_FAILURE", "false").lower() == "true"


@pytest.fixture
def client():
    """Create a test client."""
    pytest.importorskip("fastapi.testclient")
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


@pytest.fixture
def mock_service_token():
    """Mock the service token validation."""
    with patch("app.middleware.service_auth.require_service_token") as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def sample_programs():
    """Create sample program responses."""
    return [
        ProgramResponse(
            id="prog-001",
            institution_id="inst-001",
            program_name="MS Computer Science",
            degree_type=DegreeType.MASTERS,
            field="Computer Science",
            field_category="Engineering & Technology",
            description="A top CS program",
            requirements={"gpa": "3.5", "toefl": "100"},
            deadline=date.today() + timedelta(days=120),
            tuition_usd=Decimal("55000"),
            tuition_currency="USD",
            duration_months=24,
            language="English",
            mode=ProgramMode.ON_CAMPUS,
            intake="Fall",
            source_url="https://example.com",
            is_active=True,
            created_at=date.today(),
            updated_at=date.today(),
            institution_name="Massachusetts Institute of Technology",
            institution_country="United States",
            institution_rank=1,
        ),
        ProgramResponse(
            id="prog-002",
            institution_id="inst-002",
            program_name="MS Data Science",
            degree_type=DegreeType.MASTERS,
            field="Data Science",
            field_category="Technology",
            description="A data science program",
            requirements={"gpa": "3.3", "gre": "320"},
            deadline=date.today() + timedelta(days=90),
            tuition_usd=Decimal("58000"),
            tuition_currency="USD",
            duration_months=18,
            language="English",
            mode=ProgramMode.ON_CAMPUS,
            intake="Fall",
            source_url="https://example.com",
            is_active=True,
            created_at=date.today(),
            updated_at=date.today(),
            institution_name="Stanford University",
            institution_country="United States",
            institution_rank=3,
        ),
    ]


@pytest.mark.skipif(SKIP_FULL_APP_TESTS, reason="Requires running database")
class TestChatAskWithExplainability:
    """Tests for /chat/ask endpoint with explainability."""

    @pytest.mark.asyncio
    async def test_ask_returns_agent_reasoning_when_enabled(
        self, client, mock_service_token, sample_programs  # pylint: disable=unused-argument
    ):
        """Response should include agent_reasoning when include_explainability is True."""
        with (
            patch("app.api.chat.get_program_service") as mock_prog_svc,
            patch("app.api.chat.get_institution_service") as mock_inst_svc,
            patch("app.api.chat.get_llm_service") as mock_llm_svc,
        ):

            mock_prog_svc.return_value.search_programs = AsyncMock(return_value=MagicMock(items=sample_programs))
            mock_inst_svc.return_value.search_institutions = AsyncMock(return_value=MagicMock(items=[]))

            mock_llm_svc.return_value.answer_program_question = AsyncMock(
                return_value={
                    "answer": "Based on your profile, MIT's CS program is a strong match.",
                    "programs_mentioned": ["prog-001"],
                    "follow_up_suggestions": ["What are the GRE requirements?"],
                    "confidence": 0.85,
                    "model": "gpt-4o-mini",
                    "provider": "openai",
                    "agent_reasoning": {
                        "approach": "Multi-dimensional scoring applied",
                        "decision_factors": ["Student GPA: 3.8", "Target field: CS"],
                        "ranking_breakdown": [
                            {
                                "program_id": "prog-001",
                                "program_name": "MS Computer Science",
                                "university": "MIT",
                                "composite_score": 0.92,
                                "rank": 1,
                            }
                        ],
                        "filters_applied": ["GPA >= 3.5"],
                        "total_programs_evaluated": 2,
                        "total_programs_recommended": 1,
                        "confidence": 0.88,
                        "model": "gpt-4o-mini",
                        "provider": "openai",
                        "react_decision_trace": {},
                    },
                }
            )

            response = client.post(
                "/chat/ask",
                json={
                    "question": "What CS programs should I apply to?",
                    "student_profile": {
                        "field_of_interest": "Computer Science",
                        "gpa": 3.8,
                        "toefl": 110,
                    },
                    "include_explainability": True,
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert "agent_reasoning" in data
            assert data["agent_reasoning"] is not None
            assert "approach" in data["agent_reasoning"]
            assert "decision_factors" in data["agent_reasoning"]
            assert "ranking_breakdown" in data["agent_reasoning"]

    @pytest.mark.asyncio
    async def test_ask_excludes_agent_reasoning_when_disabled(
        self, client, mock_service_token, sample_programs  # pylint: disable=unused-argument
    ):
        """Response should not include agent_reasoning when include_explainability is False."""
        with (
            patch("app.api.chat.get_program_service") as mock_prog_svc,
            patch("app.api.chat.get_institution_service") as mock_inst_svc,
            patch("app.api.chat.get_llm_service") as mock_llm_svc,
        ):

            mock_prog_svc.return_value.search_programs = AsyncMock(return_value=MagicMock(items=sample_programs))
            mock_inst_svc.return_value.search_institutions = AsyncMock(return_value=MagicMock(items=[]))

            mock_llm_svc.return_value.answer_program_question = AsyncMock(
                return_value={
                    "answer": "Based on your profile, MIT's CS program is a strong match.",
                    "programs_mentioned": ["prog-001"],
                    "follow_up_suggestions": [],
                    "confidence": 0.85,
                    "model": "gpt-4o-mini",
                    "provider": "openai",
                }
            )

            response = client.post(
                "/chat/ask",
                json={
                    "question": "What CS programs should I apply to?",
                    "student_profile": {"field_of_interest": "Computer Science"},
                    "include_explainability": False,
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert data.get("agent_reasoning") is None


class TestAgentReasoningStructure:
    """Tests for agent_reasoning structure validation."""

    def test_ranking_breakdown_contains_required_fields(self):
        """Ranking breakdown entries should have all required fields."""
        from app.agents.program_discovery.program_ranking_engine import (
            apply_react_ranking_pattern,
            build_agent_reasoning,
        )

        programs = [
            {
                "id": "prog-001",
                "program_name": "MS Computer Science",
                "institution_name": "MIT",
                "institution_country": "United States",
                "institution_rank": 1,
                "field": "Computer Science",
                "requirements": {"gpa": "3.5"},
                "deadline": (date.today() + timedelta(days=100)).isoformat(),
                "tuition_usd": 55000,
            }
        ]

        profile = {"field_of_interest": "Computer Science", "gpa": 3.8}

        react_result = apply_react_ranking_pattern(programs, profile)
        reasoning = build_agent_reasoning(
            react_result=react_result,
            student_profile=profile,
            model="gpt-4o-mini",
            provider="openai",
        )

        assert len(reasoning["ranking_breakdown"]) > 0
        breakdown = reasoning["ranking_breakdown"][0]

        assert "program_id" in breakdown
        assert "program_name" in breakdown
        assert "university" in breakdown
        assert "composite_score" in breakdown
        assert "rank" in breakdown
        assert "match_scores" in breakdown
        assert "evidence" in breakdown

    def test_react_decision_trace_has_per_program_entries(self):
        """React decision trace should have entry for each program."""
        from app.agents.program_discovery.program_ranking_engine import (
            apply_react_ranking_pattern,
        )

        programs = [
            {
                "id": f"prog-{i:03d}",
                "program_name": f"Program {i}",
                "institution_name": f"University {i}",
                "institution_rank": i * 10,
                "field": "Computer Science",
                "deadline": (date.today() + timedelta(days=100)).isoformat(),
                "tuition_usd": 50000,
            }
            for i in range(1, 6)
        ]

        profile = {"field_of_interest": "Computer Science", "gpa": 3.5}

        result = apply_react_ranking_pattern(programs, profile)

        assert len(result["react_decision_trace"]) == 5
        for prog_id in ["prog-001", "prog-002", "prog-003", "prog-004", "prog-005"]:
            assert prog_id in result["react_decision_trace"]
            trace = result["react_decision_trace"][prog_id]
            assert "decision" in trace
            assert "reasons" in trace
            assert "composite_score" in trace
            assert "match_scores" in trace
            assert "evidence" in trace


class TestExplainabilityWithRankingService:
    """Tests for RankingService explainability integration."""

    @pytest.mark.asyncio
    async def test_rank_programs_with_explainability(self, sample_programs):
        """RankingService should return explainability data."""
        from app.models import ProgramRankingRequest
        from app.services.ranking_service import RankingService

        service = RankingService()

        mock_result = MagicMock()
        mock_result.items = sample_programs

        with patch.object(service._program_repo, "search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_result

            request = ProgramRankingRequest(
                student_profile={
                    "field_of_interest": "Computer Science",
                    "gpa": 3.8,
                    "toefl": 110,
                },
                target_field="Computer Science",
                target_degree=DegreeType.MASTERS,
                limit=10,
            )

            result = await service.rank_programs_with_explainability(
                request=request,
                model="gpt-4o-mini",
                provider="openai",
            )

            assert "ranked_programs" in result
            assert "agent_reasoning" in result
            assert "react_result" in result

            assert result["agent_reasoning"]["total_programs_evaluated"] == 2
            assert "ranking_breakdown" in result["agent_reasoning"]


class TestOrchestratorCompatibility:
    """Tests to ensure PDA responses are compatible with orchestrator expectations."""

    def test_agent_reasoning_structure_matches_spa_format(self):
        """Agent reasoning should match Student Profile Agent format."""
        from app.agents.program_discovery.program_ranking_engine import (
            apply_react_ranking_pattern,
            build_agent_reasoning,
        )

        programs = [
            {
                "id": "prog-001",
                "program_name": "MS CS",
                "institution_name": "MIT",
                "institution_rank": 1,
                "field": "Computer Science",
                "deadline": (date.today() + timedelta(days=100)).isoformat(),
                "tuition_usd": 55000,
            }
        ]

        profile = {"field_of_interest": "Computer Science", "gpa": 3.8}

        react_result = apply_react_ranking_pattern(programs, profile)
        reasoning = build_agent_reasoning(
            react_result=react_result,
            student_profile=profile,
            model="gpt-4o-mini",
            provider="openai",
        )

        expected_keys = {
            "approach",
            "decision_factors",
            "confidence",
            "model",
            "provider",
        }
        assert expected_keys.issubset(set(reasoning.keys()))

        assert isinstance(reasoning["decision_factors"], list)
        assert isinstance(reasoning["confidence"], float)
        assert 0 <= reasoning["confidence"] <= 1

    def test_response_can_be_serialized_to_json(self):
        """Response should be JSON serializable for orchestrator transmission."""
        import json

        from app.agents.program_discovery.program_ranking_engine import (
            apply_react_ranking_pattern,
            build_agent_reasoning,
        )

        programs = [
            {
                "id": "prog-001",
                "program_name": "MS CS",
                "institution_name": "MIT",
                "institution_rank": 1,
                "field": "Computer Science",
                "deadline": (date.today() + timedelta(days=100)).isoformat(),
                "tuition_usd": 55000,
            }
        ]

        profile = {"field_of_interest": "Computer Science"}

        react_result = apply_react_ranking_pattern(programs, profile)
        reasoning = build_agent_reasoning(
            react_result=react_result,
            student_profile=profile,
            model="gpt-4o-mini",
            provider="openai",
        )

        serialized = json.dumps(reasoning)
        deserialized = json.loads(serialized)

        assert deserialized["approach"] == reasoning["approach"]
        assert deserialized["confidence"] == reasoning["confidence"]
