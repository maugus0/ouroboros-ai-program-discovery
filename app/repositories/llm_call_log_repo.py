"""Repository for LLM call logs."""

import json
import uuid
from datetime import datetime
from typing import Any

import aiomysql

from app.core.logging import get_logger
from app.repositories.db_pool import get_pool

logger = get_logger(__name__)


class LLMCallLogRepository:
    """Repository for LLM call logging operations."""

    async def create(
        self,
        provider: str,
        model: str,
        purpose: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int | None,
        status: str,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create a new LLM call log entry.

        Args:
            provider: LLM provider (openai, anthropic, other)
            model: Model name/identifier
            purpose: Purpose of the call (e.g., "program_qa", "intent_extraction")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            latency_ms: Latency in milliseconds
            status: Call status (success, error, timeout)
            error_message: Error message if status is error
            metadata: Additional metadata as JSON

        Returns:
            The created log ID.
        """
        pool = get_pool()
        log_id = str(uuid.uuid4())

        sql = """
            INSERT INTO llm_call_logs (
                id, provider, model, purpose, input_tokens, output_tokens,
                latency_ms, status, error_message, metadata, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    sql,
                    (
                        log_id,
                        provider,
                        model,
                        purpose,
                        input_tokens,
                        output_tokens,
                        latency_ms,
                        status,
                        error_message,
                        json.dumps(metadata) if metadata else None,
                        datetime.utcnow(),
                    ),
                )

        logger.info(
            "llm_call_logged",
            log_id=log_id,
            provider=provider,
            model=model,
            purpose=purpose,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            status=status,
        )

        return log_id

    async def get_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent LLM call logs."""
        pool = get_pool()

        sql = """
            SELECT id, provider, model, purpose, input_tokens, output_tokens,
                   latency_ms, status, error_message, metadata, created_at
            FROM llm_call_logs
            ORDER BY created_at DESC
            LIMIT %s
        """

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, (limit,))
                rows = await cursor.fetchall()
                return list(rows)

    async def get_usage_stats(self, days: int = 30) -> dict[str, Any]:
        """Get usage statistics for the last N days."""
        pool = get_pool()

        sql = """
            SELECT
                provider,
                model,
                COUNT(*) as call_count,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                AVG(latency_ms) as avg_latency_ms,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count
            FROM llm_call_logs
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY provider, model
        """

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, (days,))
                rows = await cursor.fetchall()
                return {"stats": list(rows), "period_days": days}
