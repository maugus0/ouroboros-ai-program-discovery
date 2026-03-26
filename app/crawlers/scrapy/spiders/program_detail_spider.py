"""Scrapy spider for deep-scraping individual program detail pages."""

import scrapy

from app.crawlers.parsers.html_parser import program_page_metadata


class ProgramDetailSpider(scrapy.Spider):
    """Deep-scrape individual program pages for detailed metadata."""

    name = "program_detail_spider"

    def __init__(self, *args, **kwargs):
        urls = kwargs.pop("urls", None)
        super().__init__(*args, **kwargs)
        if urls:
            self.start_urls = urls if isinstance(urls, list) else [urls]

    def parse(self, response):
        """Extract detailed program metadata from a single program page."""
        yield program_page_metadata(response.text, response.url, html_length=len(response.text))
