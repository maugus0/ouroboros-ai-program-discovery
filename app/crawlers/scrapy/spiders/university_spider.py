"""Scrapy spider for batch-crawling university program listing pages."""

import scrapy

from app.crawlers.parsers.html_parser import extract_links, program_page_metadata


class UniversitySpider(scrapy.Spider):
    """Crawl university websites and extract links to individual program pages."""

    name = "university_spider"
    allowed_domains: list[str] = []

    def __init__(self, *args, **kwargs):
        start_urls = kwargs.pop("start_urls", None)
        super().__init__(*args, **kwargs)
        if start_urls:
            self.start_urls = start_urls if isinstance(start_urls, list) else [start_urls]

    def parse(self, response):
        """Extract program links from a university's programs listing page."""
        program_links = extract_links(response.text, response.url)
        self.logger.info("Found %d program links on %s", len(program_links), response.url)

        for link in program_links:
            yield scrapy.Request(url=link, callback=self.parse_program_page)

    def parse_program_page(self, response):
        """Extract basic metadata from an individual program page."""
        referer = response.request.headers.get("Referer", b"").decode("utf-8", errors="ignore")
        yield program_page_metadata(response.text, response.url, university_url=referer)
