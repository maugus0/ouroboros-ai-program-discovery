"""Service layer for institution operations."""

from app.core.logging import get_logger
from app.models import (
    InstitutionDB,
    InstitutionFromRankingData,
    InstitutionResponse,
    InstitutionSearchRequest,
    PaginatedResponse,
)
from app.repositories import InstitutionRankingRepository, InstitutionRepository

logger = get_logger(__name__)


class InstitutionService:
    """Business logic for institution operations."""

    def __init__(
        self,
        institution_repo: InstitutionRepository | None = None,
        ranking_repo: InstitutionRankingRepository | None = None,
    ):
        self._institution_repo = institution_repo or InstitutionRepository()
        self._ranking_repo = ranking_repo or InstitutionRankingRepository()

    async def get_institution(self, institution_id: str) -> InstitutionResponse:
        """Get an institution by ID with ranking information."""
        institution = await self._institution_repo.get_by_id(institution_id)
        rankings = await self._ranking_repo.get_by_institution(institution_id)

        best_rank = None
        best_rank_source = None
        if rankings:
            best = min(rankings, key=lambda r: r.rank_position)
            best_rank = best.rank_position
            best_rank_source = best.ranking_source.value

        return InstitutionResponse(
            **institution.model_dump(),
            best_rank=best_rank,
            best_rank_source=best_rank_source,
            rankings_count=len(rankings),
        )

    async def search_institutions(self, request: InstitutionSearchRequest) -> PaginatedResponse[InstitutionResponse]:
        """Search institutions with filters."""
        return await self._institution_repo.search(request)

    async def upsert_from_ranking_data(self, data: InstitutionFromRankingData) -> InstitutionDB:
        """Upsert an institution from ranking data (dedup by slug)."""
        return await self._institution_repo.upsert_from_ranking(data)

    async def get_all_countries(self) -> list[str]:
        """Get list of all countries with institutions."""
        return await self._institution_repo.get_all_countries()

    async def get_institution_count(self) -> int:
        """Get total count of active institutions."""
        return await self._institution_repo.count()

    async def get_institution_rankings(self, institution_id: str):
        """Get all rankings for an institution."""
        return await self._ranking_repo.get_by_institution(institution_id)
