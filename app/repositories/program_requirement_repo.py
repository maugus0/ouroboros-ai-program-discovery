"""Repository for program requirement database operations using raw SQL."""

import uuid

import aiomysql

from app.core.logging import get_logger
from app.models import (
    ProgramRequirementBase,
    ProgramRequirementCreate,
    ProgramRequirementDB,
)
from app.repositories.db_pool import get_pool
from app.utils.exceptions import DatabaseError, NotFoundError

logger = get_logger(__name__)


class ProgramRequirementRepository:
    """Raw SQL repository for program requirements."""

    async def create(self, data: ProgramRequirementCreate) -> ProgramRequirementDB:
        """Create a new program requirement."""
        pool = get_pool()
        requirement_id = str(uuid.uuid4())

        sql = """
            INSERT INTO program_requirements (
                id, program_id, requirement_type, requirement_name,
                requirement_value, is_mandatory, description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            requirement_id,
            data.program_id,
            data.requirement_type.value,
            data.requirement_name,
            data.requirement_value,
            data.is_mandatory,
            data.description,
        )

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql, params)
        except Exception as exc:
            logger.error("requirement_create_failed", error=str(exc))
            raise DatabaseError(f"Failed to create requirement: {exc}") from exc

        return await self.get_by_id(requirement_id)

    async def create_batch(
        self, program_id: str, requirements: list[ProgramRequirementBase]
    ) -> list[ProgramRequirementDB]:
        """Create multiple requirements for a program."""
        pool = get_pool()

        if not requirements:
            return []

        sql = """
            INSERT INTO program_requirements (
                id, program_id, requirement_type, requirement_name,
                requirement_value, is_mandatory, description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        created_ids = []
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    for req in requirements:
                        req_id = str(uuid.uuid4())
                        created_ids.append(req_id)
                        params = (
                            req_id,
                            program_id,
                            req.requirement_type.value,
                            req.requirement_name,
                            req.requirement_value,
                            req.is_mandatory,
                            req.description,
                        )
                        await cursor.execute(sql, params)
        except Exception as exc:
            logger.error("requirement_batch_create_failed", error=str(exc), program_id=program_id)
            raise DatabaseError(f"Failed to create requirements: {exc}") from exc

        return await self.get_by_program(program_id)

    async def get_by_id(self, requirement_id: str) -> ProgramRequirementDB:
        """Get a requirement by ID."""
        pool = get_pool()
        sql = "SELECT * FROM program_requirements WHERE id = %s"

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (requirement_id,))
                    row = await cursor.fetchone()
        except Exception as exc:
            logger.error("requirement_get_failed", error=str(exc), id=requirement_id)
            raise DatabaseError(f"Failed to get requirement: {exc}") from exc

        if not row:
            raise NotFoundError("Requirement")

        return ProgramRequirementDB(**row)

    async def get_by_program(self, program_id: str) -> list[ProgramRequirementDB]:
        """Get all requirements for a program."""
        pool = get_pool()
        sql = """
            SELECT * FROM program_requirements
            WHERE program_id = %s
            ORDER BY is_mandatory DESC, requirement_type, requirement_name
        """

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (program_id,))
                    rows = await cursor.fetchall()
        except Exception as exc:
            logger.error("requirements_by_program_failed", error=str(exc), program_id=program_id)
            raise DatabaseError(f"Failed to get requirements: {exc}") from exc

        return [ProgramRequirementDB(**row) for row in rows]

    async def delete_by_program(self, program_id: str) -> int:
        """Delete all requirements for a program."""
        pool = get_pool()
        sql = "DELETE FROM program_requirements WHERE program_id = %s"

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql, (program_id,))
                    return cursor.rowcount
        except Exception as exc:
            logger.error("requirements_delete_failed", error=str(exc), program_id=program_id)
            raise DatabaseError(f"Failed to delete requirements: {exc}") from exc

    async def delete(self, requirement_id: str) -> bool:
        """Delete a requirement by ID."""
        pool = get_pool()
        sql = "DELETE FROM program_requirements WHERE id = %s"

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql, (requirement_id,))
                    return cursor.rowcount > 0
        except Exception as exc:
            logger.error("requirement_delete_failed", error=str(exc), id=requirement_id)
            raise DatabaseError(f"Failed to delete requirement: {exc}") from exc
