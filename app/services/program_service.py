"""Program search, filter, and rank orchestration."""

from typing import Any, Optional

from app.config import settings
from app.core.logging import get_logger
from app.models.program import ProgramSearchRequest, StudentProfileSummary
from app.repositories.mysql_program_repo import ProgramRepository
from app.repositories.mysql_requirement_repo import RequirementRepository
from app.repositories.mysql_university_repo import UniversityRepository
from app.services.ranking_service import RankingService

logger = get_logger(__name__)


class ProgramService:
    """Business logic for program search and discovery."""

    def __init__(self):
        self.program_repo = ProgramRepository()
        self.university_repo = UniversityRepository()
        self.requirement_repo = RequirementRepository()
        self.ranking_service = RankingService()

    async def search_and_rank(self, request: ProgramSearchRequest) -> dict[str, Any]:
        """Search programs, apply ranking, and return paginated results."""
        programs = await self.program_repo.search_programs(
            field=request.field,
            degree_type=request.degree_type.value if request.degree_type else None,
            limit=request.max_results,
            offset=(request.page - 1) * request.max_results,
        )

        total = await self.program_repo.count_programs(
            field=request.field,
            degree_type=request.degree_type.value if request.degree_type else None,
        )

        if request.student_profile:
            programs = self.ranking_service.rank_programs(programs, request.student_profile)

        return {
            "programs": programs,
            "total": total,
            "page": request.page,
            "page_size": request.max_results,
        }

    async def get_program_detail(self, program_id: str) -> dict[str, Any] | None:
        """Return full program details including requirements."""
        program = await self.program_repo.get_by_id(program_id)
        if not program:
            return None

        requirements = await self.requirement_repo.get_by_program_id(program_id)
        university = await self.university_repo.get_by_id(program["university_id"])

        program["university_name"] = university["name"] if university else "Unknown"
        program["country"] = university["country"] if university else None
        program["university_ranking"] = university["ranking"] if university else None
        program["requirements_list"] = requirements

        return program

    async def get_stale_programs(self) -> list[dict[str, Any]]:
        """Return programs not crawled within the staleness threshold."""
        return await self.program_repo.get_stale_programs(settings.PROGRAM_STALENESS_DAYS)

    async def store_crawled_program(self, data: dict[str, Any]) -> str:
        """Store or update a crawled program."""
        existing = None
        if data.get("source_url"):
            results = await self.program_repo.search_programs(field=None, limit=1)
            for r in results:
                if r.get("source_url") == data["source_url"]:
                    existing = r
                    break

        if existing:
            await self.program_repo.update_program(existing["id"], data)
            logger.info("program_updated_from_crawl", program_id=existing["id"])
            return existing["id"]

        program_id = await self.program_repo.create_program(data)
        logger.info("program_created_from_crawl", program_id=program_id)
        return program_id
