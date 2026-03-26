"""Data-access layer for the universities table (raw SQL, aiomysql)."""

from typing import Any

from app.core.logging import get_logger
from app.repositories.mysql_base import MySQLBaseRepository
from app.utils.helpers import generate_uuid

logger = get_logger(__name__)


class UniversityRepository(MySQLBaseRepository):
    """CRUD operations on the ``universities`` table."""

    async def create_university(self, data: dict[str, Any]) -> str:
        """Insert a new university and return its UUID."""
        university_id = data.get("id") or generate_uuid()
        query = """
            INSERT INTO universities (
                id, name, country, ranking, website,
                programs_page_url, last_crawled
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            university_id,
            data["name"],
            data["country"],
            data.get("ranking"),
            data["website"],
            data.get("programs_page_url"),
            data.get("last_crawled"),
        )
        await self.execute_write(query, params)
        logger.info("university_created", university_id=university_id, name=data["name"])
        return university_id

    async def get_by_id(self, university_id: str) -> dict[str, Any] | None:
        """Retrieve a university by UUID."""
        query = "SELECT * FROM universities WHERE id = %s"
        return await self.execute_one(query, (university_id,))

    async def get_by_name(self, name: str) -> dict[str, Any] | None:
        """Retrieve a university by name."""
        query = "SELECT * FROM universities WHERE name = %s"
        return await self.execute_one(query, (name,))

    async def list_universities(
        self, limit: int = 50, offset: int = 0, country: str | None = None
    ) -> list[dict[str, Any]]:
        """Return a paginated list of universities, optionally filtered by country."""
        if country:
            query = "SELECT * FROM universities WHERE country = %s ORDER BY ranking ASC, name ASC LIMIT %s OFFSET %s"
            return await self.execute_query(query, (country, limit, offset))
        query = "SELECT * FROM universities ORDER BY ranking ASC, name ASC LIMIT %s OFFSET %s"
        return await self.execute_query(query, (limit, offset))

    async def count_universities(self) -> int:
        """Return the total number of universities."""
        result = await self.execute_one("SELECT COUNT(*) AS total FROM universities")
        return result["total"] if result else 0

    async def update_last_crawled(self, university_id: str) -> int:
        """Update the last_crawled timestamp for a university."""
        query = "UPDATE universities SET last_crawled = NOW() WHERE id = %s"
        return await self.execute_write(query, (university_id,))

    async def update_university(self, university_id: str, updates: dict[str, Any]) -> int:
        """Update specific fields on a university."""
        if not updates:
            return 0
        set_clauses = []
        params: list[Any] = []
        for key, value in updates.items():
            set_clauses.append(f"{key} = %s")
            params.append(value)
        params.append(university_id)
        query = f"UPDATE universities SET {', '.join(set_clauses)} WHERE id = %s"
        return await self.execute_write(query, tuple(params))
