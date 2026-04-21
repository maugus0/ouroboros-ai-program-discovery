"""Admin endpoints for monitoring and management."""

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.core.logging import get_logger
from app.middleware import require_service_token
from app.repositories.llm_call_log_repo import LLMCallLogRepository

logger = get_logger(__name__)

router = APIRouter(tags=["Admin"], prefix="/admin", dependencies=[Depends(require_service_token)])


@router.get("/llm/logs")
async def get_llm_logs(
    limit: int = Query(default=50, ge=1, le=500),
) -> dict[str, Any]:
    """Get recent LLM call logs."""
    repo = LLMCallLogRepository()
    logs = await repo.get_recent(limit=limit)

    return {
        "count": len(logs),
        "logs": [
            {
                "id": log["id"],
                "provider": log["provider"],
                "model": log["model"],
                "purpose": log["purpose"],
                "input_tokens": log["input_tokens"],
                "output_tokens": log["output_tokens"],
                "latency_ms": log["latency_ms"],
                "status": log["status"],
                "error_message": log["error_message"],
                "created_at": log["created_at"].isoformat() if log["created_at"] else None,
            }
            for log in logs
        ],
    }


@router.get("/llm/stats")
async def get_llm_stats(
    days: int = Query(default=30, ge=1, le=365),
) -> dict[str, Any]:
    """Get LLM usage statistics."""
    repo = LLMCallLogRepository()
    stats = await repo.get_usage_stats(days=days)

    return stats
