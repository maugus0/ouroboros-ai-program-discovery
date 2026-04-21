"""Health check endpoint."""

from datetime import datetime

from fastapi import APIRouter

from app.config import APP_VERSION
from app.core.logging import get_logger
from app.models import HealthResponse
from app.repositories import get_pool

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for liveness/readiness probes."""
    db_status = "disconnected"

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
                db_status = "connected"
    except Exception as exc:
        logger.warning("health_check_db_failed", error=str(exc))

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version=APP_VERSION,
        database=db_status,
        timestamp=datetime.utcnow(),
    )
