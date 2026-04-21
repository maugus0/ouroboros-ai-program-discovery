"""Repository for program database operations using raw SQL."""

import json
import uuid
from datetime import datetime
from typing import Any

import aiomysql

from app.core.logging import get_logger
from app.models import (
    PaginatedResponse,
    ProgramCreate,
    ProgramDB,
    ProgramResponse,
    ProgramSearchRequest,
    ProgramUpdate,
)
from app.repositories.db_pool import get_pool
from app.utils.exceptions import DatabaseError, NotFoundError

logger = get_logger(__name__)


class ProgramRepository:
    """Raw SQL repository for programs."""

    async def create(self, data: ProgramCreate) -> ProgramDB:
        """Create a new program."""
        pool = get_pool()
        program_id = str(uuid.uuid4())

        requirements_json = json.dumps(data.requirements) if data.requirements else None
        tuition_usd = float(data.tuition_usd) if data.tuition_usd else None
        tuition_local = float(data.tuition_local) if data.tuition_local else None

        sql = """
            INSERT INTO programs (
                id, institution_id, program_name, degree_type, field, field_category,
                description, requirements, deadline, tuition_usd, tuition_currency,
                tuition_local, duration_months, language, mode, intake, source_url,
                crawled_at, is_active
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE
            )
        """
        params = (
            program_id,
            data.institution_id,
            data.program_name,
            data.degree_type.value,
            data.field,
            data.field_category,
            data.description,
            requirements_json,
            data.deadline,
            tuition_usd,
            data.tuition_currency,
            tuition_local,
            data.duration_months,
            data.language,
            data.mode.value,
            data.intake,
            data.source_url,
            datetime.utcnow(),
        )

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql, params)
        except Exception as exc:
            logger.error("program_create_failed", error=str(exc), name=data.program_name)
            raise DatabaseError(f"Failed to create program: {exc}") from exc

        return await self.get_by_id(program_id)

    async def get_by_id(self, program_id: str) -> ProgramDB:
        """Get a program by ID."""
        pool = get_pool()
        sql = "SELECT * FROM programs WHERE id = %s"

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (program_id,))
                    row = await cursor.fetchone()
        except Exception as exc:
            logger.error("program_get_failed", error=str(exc), id=program_id)
            raise DatabaseError(f"Failed to get program: {exc}") from exc

        if not row:
            raise NotFoundError("Program")

        return self._parse_row(row)

    async def get_with_institution(self, program_id: str) -> ProgramResponse:
        """Get a program by ID with institution details."""
        pool = get_pool()
        sql = """
            SELECT p.*, i.name as institution_name, i.country as institution_country,
                (SELECT MIN(ir.rank_position) FROM institution_rankings ir WHERE ir.institution_id = p.institution_id) as institution_rank
            FROM programs p
            JOIN institutions i ON p.institution_id = i.id
            WHERE p.id = %s
        """

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (program_id,))
                    row = await cursor.fetchone()
        except Exception as exc:
            logger.error("program_get_with_institution_failed", error=str(exc), id=program_id)
            raise DatabaseError(f"Failed to get program: {exc}") from exc

        if not row:
            raise NotFoundError("Program")

        return ProgramResponse(**self._parse_row_dict(row))

    async def update(self, program_id: str, data: ProgramUpdate) -> ProgramDB:
        """Update a program."""
        pool = get_pool()

        update_fields = []
        params: list[Any] = []

        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                if field == "requirements":
                    update_fields.append(f"{field} = %s")
                    params.append(json.dumps(value))
                elif field in ("tuition_usd", "tuition_local"):
                    update_fields.append(f"{field} = %s")
                    params.append(float(value) if value else None)
                elif hasattr(value, "value"):
                    update_fields.append(f"{field} = %s")
                    params.append(value.value)
                else:
                    update_fields.append(f"{field} = %s")
                    params.append(value)

        if not update_fields:
            return await self.get_by_id(program_id)

        params.append(program_id)
        # Field names are from model schema, not user input - safe from injection
        sql = f"UPDATE programs SET {', '.join(update_fields)} WHERE id = %s"  # nosec B608

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql, params)
        except Exception as exc:
            logger.error("program_update_failed", error=str(exc), id=program_id)
            raise DatabaseError(f"Failed to update program: {exc}") from exc

        return await self.get_by_id(program_id)

    async def search(self, request: ProgramSearchRequest) -> PaginatedResponse[ProgramResponse]:
        """Search programs with filters and pagination."""
        pool = get_pool()

        where_clauses = ["p.is_active = TRUE"]
        params: list[Any] = []

        if request.query:
            where_clauses.append("(p.program_name LIKE %s OR p.description LIKE %s)")
            params.extend([f"%{request.query}%", f"%{request.query}%"])

        if request.institution_id:
            where_clauses.append("p.institution_id = %s")
            params.append(request.institution_id)

        if request.degree_type:
            where_clauses.append("p.degree_type = %s")
            params.append(request.degree_type.value)

        if request.field:
            where_clauses.append("p.field LIKE %s")
            params.append(f"%{request.field}%")

        if request.field_category:
            where_clauses.append("p.field_category = %s")
            params.append(request.field_category)

        if request.country:
            where_clauses.append("i.country = %s")
            params.append(request.country)

        if request.max_tuition_usd:
            where_clauses.append("(p.tuition_usd IS NULL OR p.tuition_usd <= %s)")
            params.append(float(request.max_tuition_usd))

        if request.deadline_after:
            where_clauses.append("(p.deadline IS NULL OR p.deadline >= %s)")
            params.append(request.deadline_after)

        if request.deadline_before:
            where_clauses.append("(p.deadline IS NULL OR p.deadline <= %s)")
            params.append(request.deadline_before)

        if request.language:
            where_clauses.append("p.language = %s")
            params.append(request.language)

        if request.mode:
            where_clauses.append("p.mode = %s")
            params.append(request.mode.value)

        ranking_join = ""
        if request.min_rank or request.max_rank:
            ranking_join = "LEFT JOIN institution_rankings ir ON p.institution_id = ir.institution_id"
            if request.min_rank:
                where_clauses.append("ir.rank_position >= %s")
                params.append(request.min_rank)
            if request.max_rank:
                where_clauses.append("ir.rank_position <= %s")
                params.append(request.max_rank)

        where_sql = " AND ".join(where_clauses)

        # Dynamic SQL parts (ranking_join, where_sql) are built from controlled code paths,
        # user input is parameterized via %s placeholders - safe from injection
        count_sql = f"""
            SELECT COUNT(DISTINCT p.id) as total
            FROM programs p
            JOIN institutions i ON p.institution_id = i.id
            {ranking_join}
            WHERE {where_sql}
        """  # nosec B608

        offset = (request.page - 1) * request.page_size
        select_sql = f"""
            SELECT DISTINCT p.*, i.name as institution_name, i.country as institution_country,
                (SELECT MIN(ir2.rank_position) FROM institution_rankings ir2 WHERE ir2.institution_id = p.institution_id) as institution_rank
            FROM programs p
            JOIN institutions i ON p.institution_id = i.id
            {ranking_join}
            WHERE {where_sql}
            ORDER BY institution_rank IS NULL, institution_rank ASC, p.program_name ASC
            LIMIT %s OFFSET %s
        """  # nosec B608

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(count_sql, params)
                    count_row = await cursor.fetchone()
                    total = count_row["total"] if count_row else 0

                    await cursor.execute(select_sql, params + [request.page_size, offset])
                    rows = await cursor.fetchall()
        except Exception as exc:
            logger.error("program_search_failed", error=str(exc))
            raise DatabaseError(f"Failed to search programs: {exc}") from exc

        items = [ProgramResponse(**self._parse_row_dict(row)) for row in rows]
        total_pages = (total + request.page_size - 1) // request.page_size if total > 0 else 1

        return PaginatedResponse(
            items=items,
            total=total,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
        )

    async def get_by_institution(self, institution_id: str) -> list[ProgramDB]:
        """Get all programs for an institution."""
        pool = get_pool()
        sql = """
            SELECT * FROM programs
            WHERE institution_id = %s AND is_active = TRUE
            ORDER BY degree_type, program_name
        """

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (institution_id,))
                    rows = await cursor.fetchall()
        except Exception as exc:
            logger.error("programs_by_institution_failed", error=str(exc), institution_id=institution_id)
            raise DatabaseError(f"Failed to get programs: {exc}") from exc

        return [self._parse_row(row) for row in rows]

    async def count(self) -> int:
        """Get total count of active programs."""
        pool = get_pool()
        sql = "SELECT COUNT(*) FROM programs WHERE is_active = TRUE"

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql)
                    row = await cursor.fetchone()
        except Exception as exc:
            logger.error("program_count_failed", error=str(exc))
            raise DatabaseError(f"Failed to count programs: {exc}") from exc

        return row[0] if row else 0

    async def get_all_fields(self) -> list[str]:
        """Get list of all unique fields."""
        pool = get_pool()
        sql = "SELECT DISTINCT field FROM programs WHERE is_active = TRUE ORDER BY field"

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql)
                    rows = await cursor.fetchall()
        except Exception as exc:
            logger.error("get_fields_failed", error=str(exc))
            raise DatabaseError(f"Failed to get fields: {exc}") from exc

        return [row[0] for row in rows]

    async def get_all_field_categories(self) -> list[str]:
        """Get list of all unique field categories."""
        pool = get_pool()
        sql = """
            SELECT DISTINCT field_category FROM programs
            WHERE is_active = TRUE AND field_category IS NOT NULL
            ORDER BY field_category
        """

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql)
                    rows = await cursor.fetchall()
        except Exception as exc:
            logger.error("get_field_categories_failed", error=str(exc))
            raise DatabaseError(f"Failed to get field categories: {exc}") from exc

        return [row[0] for row in rows]

    def _parse_row(self, row: dict[str, Any]) -> ProgramDB:
        """Parse a database row into a Pydantic model."""
        parsed = self._parse_row_dict(row)
        return ProgramDB(**parsed)

    def _parse_row_dict(self, row: dict[str, Any]) -> dict[str, Any]:
        """Parse requirements JSON if present."""
        result = dict(row)
        if result.get("requirements") and isinstance(result["requirements"], str):
            try:
                result["requirements"] = json.loads(result["requirements"])
            except json.JSONDecodeError:
                result["requirements"] = None
        return result
