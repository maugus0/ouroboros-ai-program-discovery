#!/usr/bin/env python3
"""
Enrich institution data using LLM to fill in missing fields.

This script uses OpenAI to infer missing data like:
- city (from institution name)
- website_url (official website)
- institution_type (public/private)

Usage:
    python scripts/enrich_institutions.py [--limit N] [--dry-run]
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402  # pylint: disable=C0413

load_dotenv()

from app.config import settings  # noqa: E402  # pylint: disable=C0413
from app.core.logging import get_logger, setup_logging  # noqa: E402  # pylint: disable=C0413
from app.repositories import (  # noqa: E402  # pylint: disable=C0413
    DatabasePoolConfig,
    InstitutionRepository,
    close_pool,
    create_pool,
)

setup_logging()
logger = get_logger(__name__)


async def get_institution_details_from_llm(name: str, country: str) -> dict[str, str | None]:
    """Use OpenAI to get institution details."""
    if not settings.OPENAI_API_KEY:
        logger.warning("openai_api_key_not_set")
        return {}

    try:
        import openai

        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = f"""Given the university/institution "{name}" located in "{country}", provide the following details in JSON format:

1. city: The city where the main campus is located
2. website_url: The official website URL (full URL with https://)
3. institution_type: Either "public", "private", or "private_not_for_profit"

Respond ONLY with a valid JSON object, no additional text:
{{"city": "...", "website_url": "...", "institution_type": "..."}}

If you don't know a value with certainty, use null."""

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that provides accurate information about universities and educational institutions. Respond only with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=200,
        )

        content = response.choices[0].message.content
        if content:
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(content)

    except json.JSONDecodeError as exc:
        logger.warning("llm_response_parse_error", error=str(exc), name=name)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("llm_call_failed", error=str(exc), name=name)

    return {}


async def enrich_institutions(limit: int | None = None, dry_run: bool = False) -> None:
    """Enrich institutions with missing data."""
    pool = await create_pool(
        DatabasePoolConfig(
            host=settings.get_db_host(),
            port=settings.get_db_port(),
            db=settings.get_db_name(),
            user=settings.get_db_user(),
            password=settings.get_db_password(),
        )
    )

    repo = InstitutionRepository()

    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            sql = """
                SELECT id, name, country, city, website_url, institution_type
                FROM institutions
                WHERE city IS NULL
                   OR website_url IS NULL
                   OR institution_type = 'unknown'
                ORDER BY id
            """
            if limit:
                sql += f" LIMIT {limit}"

            await cursor.execute(sql)
            rows = await cursor.fetchall()

    logger.info("institutions_to_enrich", count=len(rows))

    enriched_count = 0
    failed_count = 0

    for row in rows:
        inst_id, name, country, city, website_url, inst_type = row

        logger.info("enriching_institution", name=name, country=country)

        details = await get_institution_details_from_llm(name, country)

        if not details:
            failed_count += 1
            continue

        updates = {}
        if not city and details.get("city"):
            updates["city"] = details["city"]
        if not website_url and details.get("website_url"):
            updates["website_url"] = details["website_url"]
        if inst_type == "unknown" and details.get("institution_type"):
            inst_type_val = details["institution_type"]
            if inst_type_val in ("public", "private", "private_not_for_profit"):
                updates["institution_type"] = inst_type_val

        if updates:
            if dry_run:
                logger.info("dry_run_would_update", id=inst_id, name=name, updates=updates)
            else:
                async with pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        set_clauses = ", ".join(f"{k} = %s" for k in updates.keys())
                        sql = f"UPDATE institutions SET {set_clauses} WHERE id = %s"  # nosec B608
                        await cursor.execute(sql, (*updates.values(), inst_id))

                logger.info("institution_enriched", id=inst_id, name=name, updates=updates)
            enriched_count += 1
        else:
            logger.debug("no_updates_needed", name=name)

        await asyncio.sleep(0.5)

    await close_pool()

    logger.info(
        "enrichment_complete",
        enriched=enriched_count,
        failed=failed_count,
        total=len(rows),
        dry_run=dry_run,
    )


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Enrich institution data using LLM")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of institutions to process",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )
    args = parser.parse_args()

    asyncio.run(enrich_institutions(limit=args.limit, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
