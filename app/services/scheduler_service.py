"""Service layer for scheduled tasks (no-op for MVP)."""

from app.core.logging import get_logger

logger = get_logger(__name__)


class SchedulerService:
    """Scheduler service for background tasks (stubbed for MVP)."""

    def __init__(self):
        self._running = False

    async def start(self) -> None:
        """Start the scheduler (no-op for MVP)."""
        logger.info("scheduler_start_skipped", reason="MVP mode - no automated crawling")
        self._running = True

    async def stop(self) -> None:
        """Stop the scheduler."""
        logger.info("scheduler_stopped")
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running


_scheduler: SchedulerService | None = None


async def start_scheduler() -> None:
    """Start the global scheduler."""
    global _scheduler  # pylint: disable=global-statement
    _scheduler = SchedulerService()
    await _scheduler.start()


async def stop_scheduler() -> None:
    """Stop the global scheduler."""
    global _scheduler  # pylint: disable=global-statement
    if _scheduler:
        await _scheduler.stop()
        _scheduler = None
