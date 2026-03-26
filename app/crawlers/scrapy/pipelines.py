"""Scrapy pipelines for data validation and database storage."""

from scrapy.exceptions import DropItem

from app.core.logging import get_logger

logger = get_logger(__name__)


class ValidateProgramPipeline:
    """Validate that scraped items have the minimum required fields."""

    REQUIRED_FIELDS = ["program_name", "source_url"]

    def process_item(self, item, spider):  # pylint: disable=unused-argument
        for field in self.REQUIRED_FIELDS:
            if not item.get(field):
                raise DropItem(f"Missing required field: {field}")

        if item.get("tuition_usd") is not None:
            try:
                item["tuition_usd"] = float(item["tuition_usd"])
            except (ValueError, TypeError):
                item["tuition_usd"] = None

        if item.get("duration_years") is not None:
            try:
                item["duration_years"] = float(item["duration_years"])
            except (ValueError, TypeError):
                item["duration_years"] = None

        return item


class StoreProgramPipeline:
    """Store validated program items (placeholder for async DB writes).

    In production, this pipeline queues items for batch insertion.
    The actual DB write happens in the crawl service after the spider completes.
    """

    def __init__(self):
        self.items: list[dict] = []

    def process_item(self, item, spider):  # pylint: disable=unused-argument
        self.items.append(dict(item))
        logger.info("program_item_queued", program_name=item.get("program_name"))
        return item

    def close_spider(self, spider):
        logger.info("spider_closed", spider=spider.name, items_queued=len(self.items))
