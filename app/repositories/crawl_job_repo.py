"""Repository for crawl job database operations using raw SQL."""

import json
import uuid
from datetime import datetime
from typing import Any

import aiomysql

from app.core.logging import get_logger
from app.models import CrawlJobCreate, CrawlJobDB, CrawlJobStatus, CrawlJobUpdate
from app.repositories.db_pool import get_pool
from app.utils.exceptions import DatabaseError, NotFoundError

logger = get_logger(__name__)


class CrawlJobRepository:
    """Raw SQL repository for crawl jobs."""

    async def create(self, data: CrawlJobCreate) -> CrawlJobDB:
        """Create a new crawl job."""
        pool = get_pool()
        job_id = str(uuid.uuid4())

        metadata_json = json.dumps(data.metadata) if data.metadata else None

        sql = """
            INSERT INTO crawl_jobs (
                id, job_type, status, target_url, metadata
            ) VALUES (%s, %s, 'pending', %s, %s)
        """
        params = (job_id, data.job_type.value, data.target_url, metadata_json)

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql, params)
        except Exception as exc:
            logger.error("crawl_job_create_failed", error=str(exc))
            raise DatabaseError(f"Failed to create crawl job: {exc}") from exc

        return await self.get_by_id(job_id)

    async def get_by_id(self, job_id: str) -> CrawlJobDB:
        """Get a crawl job by ID."""
        pool = get_pool()
        sql = "SELECT * FROM crawl_jobs WHERE id = %s"

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (job_id,))
                    row = await cursor.fetchone()
        except Exception as exc:
            logger.error("crawl_job_get_failed", error=str(exc), id=job_id)
            raise DatabaseError(f"Failed to get crawl job: {exc}") from exc

        if not row:
            raise NotFoundError("CrawlJob")

        return self._parse_row(row)

    async def update(self, job_id: str, data: CrawlJobUpdate) -> CrawlJobDB:
        """Update a crawl job."""
        pool = get_pool()

        update_fields = []
        params: list[Any] = []

        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                if hasattr(value, "value"):
                    update_fields.append(f"{field} = %s")
                    params.append(value.value)
                else:
                    update_fields.append(f"{field} = %s")
                    params.append(value)

        if not update_fields:
            return await self.get_by_id(job_id)

        params.append(job_id)
        # Field names are from model schema, not user input - safe from injection
        sql = f"UPDATE crawl_jobs SET {', '.join(update_fields)} WHERE id = %s"  # nosec B608

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql, params)
        except Exception as exc:
            logger.error("crawl_job_update_failed", error=str(exc), id=job_id)
            raise DatabaseError(f"Failed to update crawl job: {exc}") from exc

        return await self.get_by_id(job_id)

    async def start(self, job_id: str) -> CrawlJobDB:
        """Mark a job as running."""
        return await self.update(
            job_id,
            CrawlJobUpdate(status=CrawlJobStatus.RUNNING, started_at=datetime.utcnow()),
        )

    async def complete(self, job_id: str, items_found: int, items_stored: int) -> CrawlJobDB:
        """Mark a job as completed."""
        return await self.update(
            job_id,
            CrawlJobUpdate(
                status=CrawlJobStatus.COMPLETED,
                items_found=items_found,
                items_stored=items_stored,
                completed_at=datetime.utcnow(),
            ),
        )

    async def fail(self, job_id: str, error_message: str) -> CrawlJobDB:
        """Mark a job as failed."""
        return await self.update(
            job_id,
            CrawlJobUpdate(
                status=CrawlJobStatus.FAILED,
                error_message=error_message,
                completed_at=datetime.utcnow(),
            ),
        )

    async def get_recent(self, limit: int = 20) -> list[CrawlJobDB]:
        """Get recent crawl jobs."""
        pool = get_pool()
        sql = """
            SELECT * FROM crawl_jobs
            ORDER BY created_at DESC
            LIMIT %s
        """

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (limit,))
                    rows = await cursor.fetchall()
        except Exception as exc:
            logger.error("crawl_jobs_get_recent_failed", error=str(exc))
            raise DatabaseError(f"Failed to get recent crawl jobs: {exc}") from exc

        return [self._parse_row(row) for row in rows]

    async def get_pending(self) -> list[CrawlJobDB]:
        """Get all pending crawl jobs."""
        pool = get_pool()
        sql = """
            SELECT * FROM crawl_jobs
            WHERE status = 'pending'
            ORDER BY created_at ASC
        """

        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql)
                    rows = await cursor.fetchall()
        except Exception as exc:
            logger.error("crawl_jobs_get_pending_failed", error=str(exc))
            raise DatabaseError(f"Failed to get pending crawl jobs: {exc}") from exc

        return [self._parse_row(row) for row in rows]

    def _parse_row(self, row: dict[str, Any]) -> CrawlJobDB:
        """Parse a database row into a Pydantic model."""
        result = dict(row)
        if result.get("metadata") and isinstance(result["metadata"], str):
            try:
                result["metadata"] = json.loads(result["metadata"])
            except json.JSONDecodeError:
                result["metadata"] = None
        return CrawlJobDB(**result)
