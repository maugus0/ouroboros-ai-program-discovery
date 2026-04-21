"""
Async MySQL connection pool using aiomysql.
Raw SQL queries — no ORM.
"""

from dataclasses import dataclass
from pathlib import Path

import aiomysql

from app.core.logging import get_logger

logger = get_logger(__name__)

_pool: aiomysql.Pool | None = None


@dataclass(frozen=True, slots=True)
class DatabasePoolConfig:
    """Parameters for creating the global aiomysql pool."""

    host: str
    port: int
    db: str
    user: str
    password: str
    pool_size: int = 10


async def create_pool(config: DatabasePoolConfig) -> aiomysql.Pool:
    """Create and cache a global connection pool."""
    global _pool  # pylint: disable=global-statement
    if _pool is not None:
        return _pool

    _pool = await aiomysql.create_pool(
        host=config.host,
        port=config.port,
        db=config.db,
        user=config.user,
        password=config.password,
        minsize=1,
        maxsize=config.pool_size,
        autocommit=True,
        charset="utf8mb4",
    )
    logger.info("database_pool_created", host=config.host, db=config.db, pool_size=config.pool_size)
    return _pool


def get_pool() -> aiomysql.Pool:
    """Return the global pool. Raises if not initialised."""
    if _pool is None:
        raise RuntimeError("Database pool has not been initialised. Call create_pool() first.")
    return _pool


async def close_pool() -> None:
    """Close the connection pool gracefully."""
    global _pool  # pylint: disable=global-statement
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None
        logger.info("database_pool_closed")


def _strip_sql_comments(sql_content: str) -> str:
    """Remove single-line SQL comments before splitting on semicolons."""
    lines = []
    for line in sql_content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        if "--" in line:
            line = line[: line.index("--")]
        lines.append(line)
    return "\n".join(lines)


async def run_migrations(pool: aiomysql.Pool) -> None:
    """Execute all SQL migration files in sorted order (idempotent)."""
    migrations_dir = Path(__file__).parent.parent.parent / "migrations"

    if not migrations_dir.exists():
        logger.warning("migrations_directory_not_found", path=str(migrations_dir))
        return

    migration_files = sorted(migrations_dir.glob("*.sql"))
    if not migration_files:
        logger.info("no_migrations_found")
        return

    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            for migration_file in migration_files:
                logger.info("running_migration", file=migration_file.name)
                sql_content = migration_file.read_text(encoding="utf-8")
                cleaned = _strip_sql_comments(sql_content)

                statements = [s.strip() for s in cleaned.split(";") if s.strip()]
                for statement in statements:
                    try:
                        await cursor.execute(statement)
                    except Exception as exc:
                        error_msg = str(exc).lower()
                        is_expected = "already exists" in error_msg or "duplicate" in error_msg
                        if is_expected:
                            logger.debug("migration_table_exists", file=migration_file.name)
                        else:
                            logger.warning(
                                "migration_statement_failed",
                                file=migration_file.name,
                                error=str(exc),
                            )

            logger.info("migrations_completed", count=len(migration_files))
