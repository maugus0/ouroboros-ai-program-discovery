"""Crawl job API endpoints (stubbed for MVP)."""

from fastapi import APIRouter, Depends

from app.core.logging import get_logger
from app.middleware import require_service_token
from app.models import CrawlJobCreate, CrawlJobDB, CrawlJobResponse, SuccessResponse
from app.repositories import CrawlJobRepository

logger = get_logger(__name__)

router = APIRouter(prefix="/crawl", tags=["Crawl"])


def get_crawl_repo() -> CrawlJobRepository:
    return CrawlJobRepository()


@router.post(
    "/jobs",
    response_model=CrawlJobResponse,
    dependencies=[Depends(require_service_token)],
)
async def create_crawl_job(
    data: CrawlJobCreate,
    repo: CrawlJobRepository = Depends(get_crawl_repo),
) -> CrawlJobDB:
    """Create a new crawl job (stubbed - jobs won't actually run in MVP)."""
    logger.info("crawl_job_created_stub", job_type=data.job_type.value)
    return await repo.create(data)


@router.get(
    "/jobs",
    response_model=list[CrawlJobResponse],
    dependencies=[Depends(require_service_token)],
)
async def get_recent_jobs(
    limit: int = 20,
    repo: CrawlJobRepository = Depends(get_crawl_repo),
) -> list[CrawlJobDB]:
    """Get recent crawl jobs."""
    return await repo.get_recent(limit)


@router.get(
    "/jobs/{job_id}",
    response_model=CrawlJobResponse,
    dependencies=[Depends(require_service_token)],
)
async def get_job(
    job_id: str,
    repo: CrawlJobRepository = Depends(get_crawl_repo),
) -> CrawlJobDB:
    """Get a crawl job by ID."""
    return await repo.get_by_id(job_id)


@router.post(
    "/trigger",
    response_model=SuccessResponse,
    dependencies=[Depends(require_service_token)],
)
async def trigger_crawl() -> SuccessResponse:
    """Trigger a crawl (stubbed for MVP - no actual crawling)."""
    logger.info("crawl_trigger_stub", message="Crawling disabled in MVP")
    return SuccessResponse(
        success=True,
        message="Crawl trigger received (no-op in MVP mode)",
    )
