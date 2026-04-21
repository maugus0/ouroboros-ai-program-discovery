"""Utility modules for the Program Discovery Agent."""

from app.utils.exceptions import (
    CrawlError,
    DatabaseError,
    LLMExtractionError,
    NotFoundError,
    ProgramDiscoveryBaseError,
    RankingError,
    ServiceAuthError,
    ValidationError,
)
from app.utils.trace_id import bind_trace_id, clear_trace_context, generate_trace_id

__all__ = [
    "CrawlError",
    "DatabaseError",
    "LLMExtractionError",
    "NotFoundError",
    "ProgramDiscoveryBaseError",
    "RankingError",
    "ServiceAuthError",
    "ValidationError",
    "bind_trace_id",
    "clear_trace_context",
    "generate_trace_id",
]
