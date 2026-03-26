"""Data-access layer for the program_requirements table (raw SQL, aiomysql)."""

from typing import Any

from app.core.logging import get_logger
from app.repositories.mysql_base import MySQLBaseRepository
from app.utils.helpers import generate_uuid

logger = get_logger(__name__)


class RequirementRepository(MySQLBaseRepository):
    """CRUD operations on the ``program_requirements`` table."""

    async def create_requirement(self, data: dict[str, Any]) -> str:
        """Insert a new program requirement and return its UUID."""
        req_id = generate_uuid()
        query = """
            INSERT INTO program_requirements (
                id, program_id, requirement_type, requirement_value, is_mandatory
            ) VALUES (%s, %s, %s, %s, %s)
        """
        params = (
            req_id,
            data["program_id"],
            data["requirement_type"],
            data["requirement_value"],
            data.get("is_mandatory", True),
        )
        await self.execute_write(query, params)
        return req_id

    async def bulk_create_requirements(self, requirements: list[dict[str, Any]]) -> int:
        """Insert multiple requirements for a program. Returns count inserted."""
        count = 0
        for req in requirements:
            await self.create_requirement(req)
            count += 1
        logger.info("requirements_bulk_created", count=count)
        return count

    async def get_by_program_id(self, program_id: str) -> list[dict[str, Any]]:
        """Return all requirements for a program."""
        query = "SELECT * FROM program_requirements WHERE program_id = %s ORDER BY requirement_type"
        return await self.execute_query(query, (program_id,))

    async def delete_by_program_id(self, program_id: str) -> int:
        """Delete all requirements for a program (used before re-crawl refresh)."""
        query = "DELETE FROM program_requirements WHERE program_id = %s"
        rows = await self.execute_write(query, (program_id,))
        logger.info("requirements_deleted", program_id=program_id, count=rows)
        return rows
