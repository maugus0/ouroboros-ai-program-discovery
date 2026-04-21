"""Base spider class for program crawling."""

import hashlib
from datetime import datetime
from typing import Any, Generator
from urllib.parse import urljoin

import scrapy
from scrapy.http import Response

from app.config import settings


class BaseProgramSpider(scrapy.Spider):
    """Base spider with common functionality for program crawling.

    All university-specific spiders should inherit from this class.
    """

    name = "base_program_spider"
    custom_settings = {
        "ROBOTSTXT_OBEY": settings.CRAWL_RESPECT_ROBOTS_TXT,
        "DOWNLOAD_DELAY": settings.CRAWL_RATE_LIMIT_DELAY,
        "USER_AGENT": settings.CRAWL_USER_AGENT,
        "DOWNLOAD_TIMEOUT": settings.CRAWL_TIMEOUT_SECONDS,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "RETRY_TIMES": 3,
        "LOG_LEVEL": "INFO",
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.crawl_job_id = kwargs.get("crawl_job_id")
        self.institution_id = kwargs.get("institution_id")
        self.institution_name = kwargs.get("institution_name", "Unknown")
        self.programs_found: list[dict] = []

    def parse(self, response: Response) -> Generator[scrapy.Request | dict, None, None]:
        """Override in subclass to implement parsing logic."""
        raise NotImplementedError("Subclasses must implement parse method")

    def extract_program_data(
        self,
        response: Response,
        program_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Extract and structure program data from a page.

        Args:
            response: The Scrapy response object.
            program_name: The name of the program.
            **kwargs: Additional program fields.

        Returns:
            Structured program data dictionary.
        """
        program_id = self._generate_program_id(self.institution_name, program_name, response.url)

        return {
            "id": program_id,
            "institution_id": self.institution_id,
            "institution_name": self.institution_name,
            "program_name": program_name,
            "source_url": response.url,
            "crawled_at": datetime.utcnow().isoformat(),
            "crawl_job_id": self.crawl_job_id,
            **kwargs,
        }

    def _generate_program_id(self, institution: str, program: str, url: str) -> str:
        """Generate a deterministic program ID for deduplication."""
        content = f"{institution}:{program}:{url}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def clean_text(self, text: str | None) -> str | None:
        """Clean and normalize extracted text."""
        if not text:
            return None
        return " ".join(text.split()).strip()

    def extract_tuition(self, text: str | None) -> int | None:
        """Extract tuition amount from text."""
        if not text:
            return None

        import re

        patterns = [
            r"\$\s*([\d,]+)",
            r"(\d{1,3}(?:,\d{3})*)\s*(?:USD|dollars?)",
            r"(?:USD|US\$)\s*([\d,]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(",", "")
                try:
                    return int(amount_str)
                except ValueError:
                    continue
        return None

    def extract_deadline(self, text: str | None) -> str | None:
        """Extract application deadline from text."""
        if not text:
            return None

        import re

        month_names = "January|February|March|April|May|June|" + "July|August|September|October|November|December"
        patterns = [
            rf"(\d{{1,2}})\s*({month_names})\s*(\d{{4}})",
            rf"({month_names})\s*(\d{{1,2}}),?\s*(\d{{4}})",
            r"(\d{4})-(\d{2})-(\d{2})",
        ]

        month_map = {
            "january": "01",
            "february": "02",
            "march": "03",
            "april": "04",
            "may": "05",
            "june": "06",
            "july": "07",
            "august": "08",
            "september": "09",
            "october": "10",
            "november": "11",
            "december": "12",
        }

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                continue
            try:
                groups = match.groups()
                if len(groups) != 3:
                    continue
                if groups[0].isdigit() and len(groups[0]) == 4:
                    return f"{groups[0]}-{groups[1]}-{groups[2]}"
                if groups[2].isdigit() and len(groups[2]) == 4:
                    if groups[1].lower() in month_map:
                        month = month_map[groups[1].lower()]
                        day = groups[0].zfill(2)
                        return f"{groups[2]}-{month}-{day}"
                    if groups[0].lower() in month_map:
                        month = month_map[groups[0].lower()]
                        day = groups[1].zfill(2)
                        return f"{groups[2]}-{month}-{day}"
            except (ValueError, IndexError):
                continue
        return None

    def extract_duration(self, text: str | None) -> int | None:
        """Extract program duration in months from text."""
        if not text:
            return None

        import re

        year_match = re.search(r"(\d+)\s*(?:year|yr)s?", text, re.IGNORECASE)
        if year_match:
            return int(year_match.group(1)) * 12

        month_match = re.search(r"(\d+)\s*months?", text, re.IGNORECASE)
        if month_match:
            return int(month_match.group(1))

        semester_match = re.search(r"(\d+)\s*semesters?", text, re.IGNORECASE)
        if semester_match:
            return int(semester_match.group(1)) * 6

        return None

    def follow_link(
        self,
        response: Response,
        url: str,
        callback: Any,
        **kwargs: Any,
    ) -> scrapy.Request:
        """Create a request to follow a link."""
        absolute_url = urljoin(response.url, url)
        return scrapy.Request(
            url=absolute_url,
            callback=callback,
            meta=kwargs,
        )
