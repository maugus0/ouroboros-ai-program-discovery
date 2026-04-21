"""Repository for institution ranking database operations using raw SQL."""

import json
import uuid
from datetime import datetime
from typing import Any

import aiomysql

from app.core.logging import get_logger
from app.models import InstitutionRankingDB, InstitutionRankingResponse, RankingUpsertData
from app.repositories.db_pool import get_pool
from app.utils.exceptions import DatabaseError, NotFoundError

logger = get_logger(__name__)


class InstitutionRankingRepository:
    """Raw SQL repository for institution rankings."""

    async def upsert(self, data: RankingUpsertData) -> InstitutionRankingDB:
        """Upsert a ranking entry (insert or update on conflict)."""
        pool = get_pool()
        ranking_id = str(uuid.uuid4())

        raw_metadata_json = json.dumps(data.raw_metadata) if data.raw_metadata else None
        overall_score = float(data.overall_score) if data.overall_score else None

        sql = """
            INSERT INTO institution_rankings (
                id, institution_id, ranking_source, ranking_year, rank_display,
                rank_position, previous_rank_display, overall_score, source_url,
                raw_metadata, crawled_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                rank_display = VALUES(rank_display),
                rank_position = VALUES(rank_position),
                previous_rank_display = VALUES(previous_rank_display),
                overall_score = VALUES(overall_score),
                source_url = VALUES(source_url),
                raw_metadata = VALUES(raw_metadata),
                crawled_at = VALUES(crawled_at)
        """
        params = (
            ranking_id,
            data.institution_id,
            data.ranking_source.value,
            data.ranking_year,
            data.rank_display,
            data.rank_position,
            data.previous_rank_display,
            overall_score,
            data.source_url,
            raw_metadata_json,
            datetime.utcnow(),
        )

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql, params)
        except Exception as exc:
            logger.error(
                "ranking_upsert_failed",
                error=str(exc),
                institution_id=data.institution_id,
            )
            raise DatabaseError(f"Failed to upsert ranking: {exc}") from exc

        return await self.get_by_institution_source_year(
            data.institution_id, data.ranking_source.value, data.ranking_year
        )

    async def get_by_id(self, ranking_id: str) -> InstitutionRankingDB:
        """Get a ranking by ID."""
        pool = get_pool()
        sql = "SELECT * FROM institution_rankings WHERE id = %s"

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (ranking_id,))
                    row = await cursor.fetchone()
        except Exception as exc:
            logger.error("ranking_get_failed", error=str(exc), id=ranking_id)
            raise DatabaseError(f"Failed to get ranking: {exc}") from exc

        if not row:
            raise NotFoundError("Ranking")

        return self._parse_row(row)

    async def get_by_institution_source_year(
        self, institution_id: str, ranking_source: str, ranking_year: int
    ) -> InstitutionRankingDB:
        """Get a ranking by institution, source, and year."""
        pool = get_pool()
        sql = """
            SELECT * FROM institution_rankings
            WHERE institution_id = %s AND ranking_source = %s AND ranking_year = %s
        """

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (institution_id, ranking_source, ranking_year))
                    row = await cursor.fetchone()
        except Exception as exc:
            logger.error(
                "ranking_get_by_key_failed",
                error=str(exc),
                institution_id=institution_id,
            )
            raise DatabaseError(f"Failed to get ranking: {exc}") from exc

        if not row:
            raise NotFoundError("Ranking")

        return self._parse_row(row)

    async def get_by_institution(self, institution_id: str) -> list[InstitutionRankingDB]:
        """Get all rankings for an institution."""
        pool = get_pool()
        sql = """
            SELECT * FROM institution_rankings
            WHERE institution_id = %s
            ORDER BY ranking_year DESC, ranking_source
        """

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (institution_id,))
                    rows = await cursor.fetchall()
        except Exception as exc:
            logger.error(
                "ranking_get_by_institution_failed",
                error=str(exc),
                institution_id=institution_id,
            )
            raise DatabaseError(f"Failed to get rankings: {exc}") from exc

        return [self._parse_row(row) for row in rows]

    async def get_best_rank(self, institution_id: str) -> int | None:
        """Get the best (lowest) rank position for an institution across all sources."""
        pool = get_pool()
        sql = """
            SELECT MIN(rank_position) as best_rank
            FROM institution_rankings
            WHERE institution_id = %s
        """

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (institution_id,))
                    row = await cursor.fetchone()
        except Exception as exc:
            logger.error(
                "best_rank_get_failed",
                error=str(exc),
                institution_id=institution_id,
            )
            raise DatabaseError(f"Failed to get best rank: {exc}") from exc

        return row["best_rank"] if row and row["best_rank"] else None

    async def get_rankings_by_source_year(
        self, ranking_source: str, ranking_year: int, limit: int = 100, offset: int = 0
    ) -> list[InstitutionRankingResponse]:
        """Get rankings for a specific source and year with institution details."""
        pool = get_pool()
        sql = """
            SELECT ir.*, i.name as institution_name, i.country as institution_country
            FROM institution_rankings ir
            JOIN institutions i ON ir.institution_id = i.id
            WHERE ir.ranking_source = %s AND ir.ranking_year = %s
            ORDER BY ir.rank_position
            LIMIT %s OFFSET %s
        """

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (ranking_source, ranking_year, limit, offset))
                    rows = await cursor.fetchall()
        except Exception as exc:
            logger.error(
                "rankings_by_source_year_failed",
                error=str(exc),
                source=ranking_source,
                year=ranking_year,
            )
            raise DatabaseError(f"Failed to get rankings: {exc}") from exc

        return [InstitutionRankingResponse(**self._parse_row_dict(row)) for row in rows]

    async def count_by_source_year(self, ranking_source: str, ranking_year: int) -> int:
        """Count rankings for a specific source and year."""
        pool = get_pool()
        sql = """
            SELECT COUNT(*) as count
            FROM institution_rankings
            WHERE ranking_source = %s AND ranking_year = %s
        """

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (ranking_source, ranking_year))
                    row = await cursor.fetchone()
        except Exception as exc:
            logger.error(
                "rankings_count_failed",
                error=str(exc),
                source=ranking_source,
                year=ranking_year,
            )
            raise DatabaseError(f"Failed to count rankings: {exc}") from exc

        return row["count"] if row else 0

    def _parse_row(self, row: dict[str, Any]) -> InstitutionRankingDB:
        """Parse a database row into a Pydantic model."""
        parsed = self._parse_row_dict(row)
        return InstitutionRankingDB(**parsed)

    def _parse_row_dict(self, row: dict[str, Any]) -> dict[str, Any]:
        """Parse raw_metadata JSON if present."""
        result = dict(row)
        if result.get("raw_metadata") and isinstance(result["raw_metadata"], str):
            try:
                result["raw_metadata"] = json.loads(result["raw_metadata"])
            except json.JSONDecodeError:
                result["raw_metadata"] = None
        return result
