"""Data-access layer for the programs table (raw SQL, aiomysql)."""

import json
from typing import Any

from app.core.logging import get_logger
from app.repositories.mysql_base import MySQLBaseRepository
from app.utils.helpers import generate_uuid

logger = get_logger(__name__)


class ProgramRepository(MySQLBaseRepository):
    """CRUD operations on the ``programs`` table."""

    async def create_program(self, data: dict[str, Any]) -> str:
        """Insert a new program and return its UUID."""
        program_id = data.get("id") or generate_uuid()
        query = """
            INSERT INTO programs (
                id, university_id, program_name, degree_type, field,
                field_category, description, requirements, deadline,
                tuition_usd, duration_years, ranking_score,
                source_url, crawled_at, is_active
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s
            )
        """
        params = (
            program_id,
            data["university_id"],
            data["program_name"],
            data["degree_type"],
            data["field"],
            data.get("field_category"),
            data.get("description"),
            json.dumps(data.get("requirements")) if data.get("requirements") else None,
            data.get("deadline"),
            data.get("tuition_usd"),
            data.get("duration_years"),
            data.get("ranking_score"),
            data["source_url"],
            data.get("crawled_at"),
            data.get("is_active", True),
        )
        await self.execute_write(query, params)
        logger.info("program_created", program_id=program_id, name=data["program_name"])
        return program_id

    async def get_by_id(self, program_id: str) -> dict[str, Any] | None:
        """Retrieve a program by UUID."""
        query = "SELECT * FROM programs WHERE id = %s"
        return await self.execute_one(query, (program_id,))

    async def search_programs(
        self,
        field: str | None = None,
        degree_type: str | None = None,
        university_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Search programs with optional filters."""
        conditions = ["is_active = TRUE"]
        params: list[Any] = []

        if field:
            conditions.append("(field LIKE %s OR MATCH(program_name, description) AGAINST(%s IN BOOLEAN MODE))")
            params.extend([f"%{field}%", field])

        if degree_type:
            conditions.append("degree_type = %s")
            params.append(degree_type)

        if university_id:
            conditions.append("university_id = %s")
            params.append(university_id)

        where_clause = " AND ".join(conditions)
        params.extend([limit, offset])

        query = f"""
            SELECT p.*, u.name AS university_name, u.country, u.ranking AS university_ranking
            FROM programs p
            JOIN universities u ON p.university_id = u.id
            WHERE {where_clause}
            ORDER BY p.ranking_score DESC, u.ranking ASC
            LIMIT %s OFFSET %s
        """  # nosec B608
        return await self.execute_query(query, tuple(params))

    async def count_programs(self, field: str | None = None, degree_type: str | None = None) -> int:
        """Count programs matching filters."""
        conditions = ["is_active = TRUE"]
        params: list[Any] = []

        if field:
            conditions.append("field LIKE %s")
            params.append(f"%{field}%")

        if degree_type:
            conditions.append("degree_type = %s")
            params.append(degree_type)

        where_clause = " AND ".join(conditions)
        query = f"SELECT COUNT(*) AS total FROM programs WHERE {where_clause}"  # nosec B608
        result = await self.execute_one(query, tuple(params))
        return result["total"] if result else 0

    async def get_stale_programs(self, staleness_days: int = 30) -> list[dict[str, Any]]:
        """Return programs not crawled within the staleness threshold."""
        query = """
            SELECT p.*, u.name AS university_name, u.website AS university_website
            FROM programs p
            JOIN universities u ON p.university_id = u.id
            WHERE p.is_active = TRUE
              AND p.crawled_at < DATE_SUB(NOW(), INTERVAL %s DAY)
            ORDER BY p.crawled_at ASC
        """
        return await self.execute_query(query, (staleness_days,))

    async def update_program(self, program_id: str, updates: dict[str, Any]) -> int:
        """Update specific fields on a program."""
        if not updates:
            return 0
        json_fields = {"requirements"}
        set_clauses = []
        params: list[Any] = []
        for key, value in updates.items():
            set_clauses.append(f"{key} = %s")
            params.append(json.dumps(value) if key in json_fields else value)
        params.append(program_id)
        query = f"UPDATE programs SET {', '.join(set_clauses)} WHERE id = %s"  # nosec B608
        rows = await self.execute_write(query, tuple(params))
        logger.info("program_updated", program_id=program_id, fields=list(updates.keys()))
        return rows

    async def deactivate_program(self, program_id: str) -> int:
        """Mark a program as inactive (soft delete)."""
        query = "UPDATE programs SET is_active = FALSE WHERE id = %s"
        return await self.execute_write(query, (program_id,))

    async def get_programs_by_university(self, university_id: str) -> list[dict[str, Any]]:
        """Return all active programs for a university."""
        query = "SELECT * FROM programs WHERE university_id = %s AND is_active = TRUE ORDER BY program_name"
        return await self.execute_query(query, (university_id,))
