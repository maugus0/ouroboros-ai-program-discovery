"""Repository for institution database operations using raw SQL."""

import re
import uuid
from typing import Any

import aiomysql

from app.core.logging import get_logger
from app.models import (
    InstitutionDB,
    InstitutionFromRankingData,
    InstitutionResponse,
    InstitutionSearchRequest,
    PaginatedResponse,
)
from app.repositories.db_pool import get_pool
from app.utils.exceptions import DatabaseError, NotFoundError

logger = get_logger(__name__)


def _generate_slug(name: str, country: str) -> str:
    """Generate a URL-safe slug from institution name and country."""
    combined = f"{name}-{country}".lower()
    slug = re.sub(r"[^a-z0-9]+", "-", combined)
    slug = slug.strip("-")
    return slug[:512]


class InstitutionRepository:
    """Raw SQL repository for institutions."""

    async def create(self, data: InstitutionFromRankingData) -> InstitutionDB:
        """Create a new institution."""
        pool = get_pool()
        institution_id = str(uuid.uuid4())
        slug = _generate_slug(data.name, data.country)

        sql = """
            INSERT INTO institutions (
                id, name, slug, country, city, region, website_url, logo_url,
                institution_type, size, focus, research_output, status, is_active
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'verified', TRUE
            )
        """
        params = (
            institution_id,
            data.name,
            slug,
            data.country,
            data.city,
            data.region,
            data.website_url,
            None,
            data.institution_type.value,
            data.size.value,
            data.focus.value,
            data.research_output.value,
        )

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql, params)
        except Exception as exc:
            logger.error("institution_create_failed", error=str(exc), name=data.name)
            raise DatabaseError(f"Failed to create institution: {exc}") from exc

        return await self.get_by_id(institution_id)

    async def upsert_from_ranking(self, data: InstitutionFromRankingData) -> InstitutionDB:
        """Upsert an institution from ranking data (dedup by slug)."""
        slug = _generate_slug(data.name, data.country)

        existing = await self.get_by_slug(slug)
        if existing:
            return existing

        return await self.create(data)

    async def get_by_id(self, institution_id: str) -> InstitutionDB:
        """Get an institution by ID."""
        pool = get_pool()
        sql = "SELECT * FROM institutions WHERE id = %s"

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (institution_id,))
                    row = await cursor.fetchone()
        except Exception as exc:
            logger.error("institution_get_failed", error=str(exc), id=institution_id)
            raise DatabaseError(f"Failed to get institution: {exc}") from exc

        if not row:
            raise NotFoundError("Institution")

        return InstitutionDB(**row)

    async def get_by_slug(self, slug: str) -> InstitutionDB | None:
        """Get an institution by slug."""
        pool = get_pool()
        sql = "SELECT * FROM institutions WHERE slug = %s"

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (slug,))
                    row = await cursor.fetchone()
        except Exception as exc:
            logger.error("institution_get_by_slug_failed", error=str(exc), slug=slug)
            raise DatabaseError(f"Failed to get institution by slug: {exc}") from exc

        if not row:
            return None

        return InstitutionDB(**row)

    async def search(self, request: InstitutionSearchRequest) -> PaginatedResponse[InstitutionResponse]:
        """Search institutions with filters and pagination."""
        pool = get_pool()

        where_clauses = ["i.is_active = TRUE"]
        params: list[Any] = []

        if request.query:
            where_clauses.append("i.name LIKE %s")
            params.append(f"%{request.query}%")

        if request.country:
            where_clauses.append("i.country = %s")
            params.append(request.country)

        if request.institution_type:
            where_clauses.append("i.institution_type = %s")
            params.append(request.institution_type.value)

        join_clause = ""
        if request.min_rank or request.max_rank or request.ranking_source or request.ranking_year:
            join_clause = "LEFT JOIN institution_rankings ir ON i.id = ir.institution_id"
            if request.ranking_source:
                where_clauses.append("ir.ranking_source = %s")
                params.append(request.ranking_source)
            if request.ranking_year:
                where_clauses.append("ir.ranking_year = %s")
                params.append(request.ranking_year)
            if request.min_rank:
                where_clauses.append("ir.rank_position >= %s")
                params.append(request.min_rank)
            if request.max_rank:
                where_clauses.append("ir.rank_position <= %s")
                params.append(request.max_rank)

        where_sql = " AND ".join(where_clauses)

        # Dynamic SQL parts (join_clause, where_sql) are built from controlled code paths,
        # user input is parameterized via %s placeholders - safe from injection
        count_sql = f"""
            SELECT COUNT(DISTINCT i.id) as total
            FROM institutions i
            {join_clause}
            WHERE {where_sql}
        """  # nosec B608

        offset = (request.page - 1) * request.page_size
        select_sql = f"""
            SELECT DISTINCT i.*,
                (SELECT MIN(ir2.rank_position) FROM institution_rankings ir2 WHERE ir2.institution_id = i.id) as best_rank,
                (SELECT ir3.ranking_source FROM institution_rankings ir3 WHERE ir3.institution_id = i.id ORDER BY ir3.rank_position LIMIT 1) as best_rank_source,
                (SELECT COUNT(*) FROM institution_rankings ir4 WHERE ir4.institution_id = i.id) as rankings_count
            FROM institutions i
            {join_clause}
            WHERE {where_sql}
            ORDER BY best_rank ASC NULLS LAST, i.name ASC
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
            logger.error("institution_search_failed", error=str(exc))
            raise DatabaseError(f"Failed to search institutions: {exc}") from exc

        items = [InstitutionResponse(**row) for row in rows]
        total_pages = (total + request.page_size - 1) // request.page_size if total > 0 else 1

        return PaginatedResponse(
            items=items,
            total=total,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
        )

    async def get_all_countries(self) -> list[str]:
        """Get list of all unique countries with institutions."""
        pool = get_pool()
        sql = "SELECT DISTINCT country FROM institutions WHERE is_active = TRUE ORDER BY country"

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql)
                    rows = await cursor.fetchall()
        except Exception as exc:
            logger.error("get_countries_failed", error=str(exc))
            raise DatabaseError(f"Failed to get countries: {exc}") from exc

        return [row[0] for row in rows]

    async def count(self) -> int:
        """Get total count of active institutions."""
        pool = get_pool()
        sql = "SELECT COUNT(*) FROM institutions WHERE is_active = TRUE"

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql)
                    row = await cursor.fetchone()
        except Exception as exc:
            logger.error("institution_count_failed", error=str(exc))
            raise DatabaseError(f"Failed to count institutions: {exc}") from exc

        return row[0] if row else 0
