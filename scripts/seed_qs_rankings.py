#!/usr/bin/env python3
"""
Seed QS World University Rankings 2026 into the database.

Usage:
    python scripts/seed_qs_rankings.py
"""

import asyncio
import json
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from app.config import settings
from app.core.logging import get_logger, setup_logging
from app.models import (
    InstitutionFromRankingData,
    InstitutionFocus,
    InstitutionSize,
    InstitutionType,
    RankingSource,
    RankingUpsertData,
    ResearchOutput,
)
from app.repositories import (
    DatabasePoolConfig,
    InstitutionRankingRepository,
    InstitutionRepository,
    close_pool,
    create_pool,
    run_migrations,
)

setup_logging()
logger = get_logger(__name__)


def map_size(size_str: str | None) -> InstitutionSize:
    """Map QS size string to enum."""
    if not size_str:
        return InstitutionSize.UNKNOWN
    size_lower = size_str.lower()
    if "xl" in size_lower or "extra" in size_lower:
        return InstitutionSize.EXTRA_LARGE
    if "l" in size_lower or "large" in size_lower:
        return InstitutionSize.LARGE
    if "m" in size_lower or "medium" in size_lower:
        return InstitutionSize.MEDIUM
    if "s" in size_lower or "small" in size_lower:
        return InstitutionSize.SMALL
    return InstitutionSize.UNKNOWN


def map_focus(focus_str: str | None) -> InstitutionFocus:
    """Map QS focus string to enum."""
    if not focus_str:
        return InstitutionFocus.UNKNOWN
    focus_lower = focus_str.lower()
    if "comprehensive" in focus_lower or "fc" in focus_lower:
        return InstitutionFocus.FULL_COMPREHENSIVE
    if "focused" in focus_lower or "fo" in focus_lower:
        return InstitutionFocus.FOCUSED
    if "specialist" in focus_lower or "sp" in focus_lower:
        return InstitutionFocus.SPECIALIST
    return InstitutionFocus.UNKNOWN


def map_research_output(output_str: str | None) -> ResearchOutput:
    """Map QS research output string to enum."""
    if not output_str:
        return ResearchOutput.UNKNOWN
    output_lower = output_str.lower()
    if "very high" in output_lower or "vh" in output_lower:
        return ResearchOutput.VERY_HIGH
    if "high" in output_lower or "hi" in output_lower:
        return ResearchOutput.HIGH
    if "medium" in output_lower or "md" in output_lower:
        return ResearchOutput.MEDIUM
    if "low" in output_lower or "lo" in output_lower:
        return ResearchOutput.LOW
    if "very low" in output_lower or "vl" in output_lower:
        return ResearchOutput.VERY_LOW
    return ResearchOutput.UNKNOWN


async def seed_qs_rankings():
    """Seed QS rankings from JSON file."""
    data_file = Path(__file__).parent.parent / "data" / "qs_world_rankings_2026.json"
    
    if not data_file.exists():
        logger.error("qs_data_file_not_found", path=str(data_file))
        logger.info("run_generate_first", command="python scripts/generate_qs_json.py")
        return
    
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    pool = await create_pool(
        DatabasePoolConfig(
            host=settings.get_db_host(),
            port=settings.get_db_port(),
            db=settings.get_db_name(),
            user=settings.get_db_user(),
            password=settings.get_db_password(),
        )
    )
    
    await run_migrations(pool)
    
    institution_repo = InstitutionRepository()
    ranking_repo = InstitutionRankingRepository()
    
    ranking_source = RankingSource(data["ranking_source"])
    ranking_year = data["ranking_year"]
    source_url = data.get("source_url")
    
    institutions_created = 0
    rankings_created = 0
    
    for item in data["institutions"]:
        try:
            institution_data = InstitutionFromRankingData(
                name=item["name"],
                country=item["country"],
                city=item.get("city"),
                region=item.get("region"),
                website_url=item.get("website_url"),
                institution_type=InstitutionType.UNKNOWN,
                size=map_size(item.get("size")),
                focus=map_focus(item.get("focus")),
                research_output=map_research_output(item.get("research_output")),
            )
            
            institution = await institution_repo.upsert_from_ranking(institution_data)
            institutions_created += 1
            
            ranking_data = RankingUpsertData(
                institution_id=institution.id,
                ranking_source=ranking_source,
                ranking_year=ranking_year,
                rank_display=item["rank_display"],
                rank_position=item["rank_position"],
                previous_rank_display=item.get("previous_rank_display"),
                overall_score=Decimal(str(item["overall_score"])) if item.get("overall_score") else None,
                source_url=source_url,
                raw_metadata=item.get("indicators"),
            )
            
            await ranking_repo.upsert(ranking_data)
            rankings_created += 1
            
            if rankings_created % 100 == 0:
                logger.info("seed_progress", institutions=institutions_created, rankings=rankings_created)
                
        except Exception as exc:
            logger.error("seed_item_failed", error=str(exc), name=item.get("name"))
            continue
    
    await close_pool()
    
    logger.info(
        "seed_completed",
        institutions=institutions_created,
        rankings=rankings_created,
    )


if __name__ == "__main__":
    asyncio.run(seed_qs_rankings())
