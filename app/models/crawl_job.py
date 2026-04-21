"""Pydantic models for crawl jobs."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import CrawlJobStatus, CrawlJobType


class CrawlJobBase(BaseModel):
    """Base crawl job fields."""

    job_type: CrawlJobType
    target_url: str | None = Field(None, max_length=512)
    metadata: dict[str, Any] | None = None


class CrawlJobCreate(CrawlJobBase):
    """Request model for creating a crawl job."""

    pass


class CrawlJobDB(CrawlJobBase):
    """Crawl job as stored in the database."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: CrawlJobStatus = CrawlJobStatus.PENDING
    items_found: int = 0
    items_stored: int = 0
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class CrawlJobUpdate(BaseModel):
    """Update fields for a crawl job."""

    status: CrawlJobStatus | None = None
    items_found: int | None = None
    items_stored: int | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class CrawlJobResponse(CrawlJobDB):
    """Crawl job response."""

    duration_seconds: float | None = None

    @property
    def computed_duration(self) -> float | None:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
