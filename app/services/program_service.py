"""Service layer for program operations."""

from app.core.logging import get_logger
from app.models import (
    PaginatedResponse,
    ProgramCreate,
    ProgramDB,
    ProgramRequirementBase,
    ProgramResponse,
    ProgramSearchRequest,
    ProgramUpdate,
)
from app.repositories import ProgramRepository, ProgramRequirementRepository

logger = get_logger(__name__)


class ProgramService:
    """Business logic for program operations."""

    def __init__(
        self,
        program_repo: ProgramRepository | None = None,
        requirement_repo: ProgramRequirementRepository | None = None,
    ):
        self._program_repo = program_repo or ProgramRepository()
        self._requirement_repo = requirement_repo or ProgramRequirementRepository()

    async def create_program(
        self,
        data: ProgramCreate,
        requirements: list[ProgramRequirementBase] | None = None,
    ) -> ProgramResponse:
        """Create a new program with optional requirements."""
        program = await self._program_repo.create(data)

        if requirements:
            await self._requirement_repo.create_batch(program.id, requirements)

        return await self._program_repo.get_with_institution(program.id)

    async def get_program(self, program_id: str) -> ProgramResponse:
        """Get a program by ID with institution details."""
        return await self._program_repo.get_with_institution(program_id)

    async def update_program(self, program_id: str, data: ProgramUpdate) -> ProgramResponse:
        """Update a program."""
        await self._program_repo.update(program_id, data)
        return await self._program_repo.get_with_institution(program_id)

    async def search_programs(self, request: ProgramSearchRequest) -> PaginatedResponse[ProgramResponse]:
        """Search programs with filters."""
        return await self._program_repo.search(request)

    async def get_programs_by_institution(self, institution_id: str) -> list[ProgramDB]:
        """Get all programs for an institution."""
        return await self._program_repo.get_by_institution(institution_id)

    async def get_program_requirements(self, program_id: str):
        """Get all requirements for a program."""
        return await self._requirement_repo.get_by_program(program_id)

    async def set_program_requirements(self, program_id: str, requirements: list[ProgramRequirementBase]):
        """Replace all requirements for a program."""
        await self._requirement_repo.delete_by_program(program_id)
        return await self._requirement_repo.create_batch(program_id, requirements)

    async def get_program_count(self) -> int:
        """Get total count of active programs."""
        return await self._program_repo.count()

    async def get_all_fields(self) -> list[str]:
        """Get list of all unique fields."""
        return await self._program_repo.get_all_fields()

    async def get_all_field_categories(self) -> list[str]:
        """Get list of all unique field categories."""
        return await self._program_repo.get_all_field_categories()
