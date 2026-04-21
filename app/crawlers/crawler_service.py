"""Service for managing crawl jobs and running spiders."""

from datetime import datetime, timedelta
from typing import Any

from app.config import settings
from app.core.logging import get_logger
from app.models import CrawlJobCreate, CrawlJobType
from app.repositories import CrawlJobRepository, ProgramRepository

logger = get_logger(__name__)


class CrawlerService:
    """Service for managing program crawling operations."""

    def __init__(self) -> None:
        self.crawl_job_repo = CrawlJobRepository()
        self.program_repo = ProgramRepository()

    async def create_crawl_job(
        self,
        job_type: CrawlJobType = CrawlJobType.PROGRAM_LIST,
        target_url: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create a new crawl job.

        Args:
            job_type: Type of crawl job.
            target_url: Optional URL to crawl.
            metadata: Optional metadata for the job.

        Returns:
            The created crawl job ID.
        """
        job_data = CrawlJobCreate(
            job_type=job_type,
            target_url=target_url,
            metadata=metadata,
        )
        job = await self.crawl_job_repo.create(job_data)
        return job.id

    async def run_crawl_job(self, job_id: str) -> dict[str, Any]:
        """Run a crawl job.

        Note: In production, this would spawn a Scrapy process.
        For now, this is a stub that updates job status.

        Args:
            job_id: The crawl job ID to run.

        Returns:
            Job result summary.
        """
        job = await self.crawl_job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Crawl job {job_id} not found")

        await self.crawl_job_repo.start(job_id)

        logger.info(
            "crawl_job_started",
            job_id=job_id,
            job_type=job.job_type.value,
        )

        try:
            items_found = 0
            items_stored = 0

            await self.crawl_job_repo.complete(job_id, items_found, items_stored)

            logger.info(
                "crawl_job_completed",
                job_id=job_id,
                items_found=items_found,
                items_stored=items_stored,
            )

            return {
                "job_id": job_id,
                "status": "completed",
                "items_found": items_found,
                "items_stored": items_stored,
            }

        except Exception as exc:
            error_msg = str(exc)
            await self.crawl_job_repo.fail(job_id, error_msg)

            logger.error("crawl_job_failed", job_id=job_id, error=error_msg)
            raise

    async def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        """Get the status of a crawl job.

        Args:
            job_id: The crawl job ID.

        Returns:
            Job status dictionary or None if not found.
        """
        try:
            job = await self.crawl_job_repo.get_by_id(job_id)
        except Exception:
            return None

        return {
            "job_id": job.id,
            "status": job.status.value,
            "job_type": job.job_type.value,
            "items_found": job.items_found,
            "items_stored": job.items_stored,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
        }

    async def get_stale_program_count(self) -> int:
        """Get count of programs that haven't been updated recently.

        Note: This is a placeholder - actual implementation would query
        programs where crawled_at < stale_threshold.

        Returns:
            Count of stale programs.
        """
        # Placeholder: actual implementation would need a database query
        _ = datetime.utcnow() - timedelta(days=settings.CRAWL_STALE_DAYS)
        return 0
