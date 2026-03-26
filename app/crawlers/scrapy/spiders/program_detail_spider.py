"""Scrapy spider for deep-scraping individual program detail pages."""

import scrapy

from app.crawlers.parsers.html_parser import extract_basic_metadata


class ProgramDetailSpider(scrapy.Spider):
    """Deep-scrape individual program pages for detailed metadata."""

    name = "program_detail_spider"

    def __init__(self, urls=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if urls:
            self.start_urls = urls if isinstance(urls, list) else [urls]

    def parse(self, response, **kwargs):
        """Extract detailed program metadata from a single program page."""
        metadata = extract_basic_metadata(response.text)
        metadata["source_url"] = response.url
        metadata["html_length"] = len(response.text)

        yield metadata
