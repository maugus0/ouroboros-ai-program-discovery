"""Generic university program spider with configurable selectors."""

from typing import Any, Generator

import scrapy
from scrapy.http import Response

from app.crawlers.scrapy.spiders.base_spider import BaseProgramSpider


class UniversityProgramSpider(BaseProgramSpider):
    """Configurable spider for crawling university program pages.

    This spider can be configured with CSS/XPath selectors for different
    university websites through the university_config parameter.
    """

    name = "university_program_spider"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.config = kwargs.get("university_config", {})
        self.start_urls = kwargs.get("start_urls", [])

    def parse(self, response: Response) -> Generator[scrapy.Request | dict, None, None]:
        """Parse the program listing page."""
        program_links_selector = self.config.get(
            "program_links_selector", "a[href*='program'], a[href*='degree'], a[href*='graduate']"
        )

        for link in response.css(program_links_selector):
            href = link.attrib.get("href")
            if href:
                yield self.follow_link(
                    response,
                    href,
                    callback=self.parse_program_page,
                )

        next_page_selector = self.config.get("next_page_selector")
        if next_page_selector:
            next_page = response.css(next_page_selector).attrib.get("href")
            if next_page:
                yield self.follow_link(response, next_page, callback=self.parse)

    def parse_program_page(self, response: Response) -> Generator[dict, None, None]:
        """Parse an individual program page."""
        program_name = self._extract_field(
            response,
            self.config.get("program_name_selector", "h1::text"),
        )

        if not program_name:
            return

        degree_type = self._extract_field(
            response,
            self.config.get("degree_type_selector"),
        ) or self._infer_degree_type(program_name)

        description = self._extract_field(
            response,
            self.config.get("description_selector", "meta[name='description']::attr(content)"),
        )

        tuition_text = self._extract_field(
            response,
            self.config.get("tuition_selector"),
        )
        tuition = self.extract_tuition(tuition_text) if tuition_text else None

        deadline_text = self._extract_field(
            response,
            self.config.get("deadline_selector"),
        )
        deadline = self.extract_deadline(deadline_text) if deadline_text else None

        duration_text = self._extract_field(
            response,
            self.config.get("duration_selector"),
        )
        duration = self.extract_duration(duration_text) if duration_text else None

        field = self._extract_field(
            response,
            self.config.get("field_selector"),
        )

        requirements = self._extract_requirements(response)

        program_data = self.extract_program_data(
            response,
            program_name=program_name,
            degree_type=degree_type,
            description=self.clean_text(description),
            tuition_usd=tuition,
            deadline=deadline,
            duration_months=duration,
            field=field,
            field_category=self._categorize_field(field),
            requirements=requirements,
            language="English",
            mode="on_campus",
            status="active",
        )

        self.programs_found.append(program_data)
        yield program_data

    def _extract_field(self, response: Response, selector: str | None) -> str | None:
        """Extract a field using CSS selector."""
        if not selector:
            return None
        value = response.css(selector).get()
        return self.clean_text(value) if value else None

    def _extract_requirements(self, response: Response) -> list[dict]:
        """Extract program requirements."""
        requirements = []
        req_selector = self.config.get("requirements_selector")

        if req_selector:
            for req in response.css(req_selector):
                req_text = self.clean_text(req.css("::text").get())
                if req_text:
                    requirements.append(
                        {
                            "type": self._classify_requirement(req_text),
                            "description": req_text,
                        }
                    )

        return requirements

    def _classify_requirement(self, text: str) -> str:
        """Classify a requirement based on its text."""
        text_lower = text.lower()
        if any(term in text_lower for term in ["gpa", "grade", "academic"]):
            return "gpa"
        if any(term in text_lower for term in ["gre", "gmat", "test score"]):
            return "test_score"
        if any(term in text_lower for term in ["toefl", "ielts", "english"]):
            return "language"
        if any(term in text_lower for term in ["degree", "bachelor", "undergraduate"]):
            return "degree"
        if any(term in text_lower for term in ["experience", "work", "research"]):
            return "experience"
        return "other"

    def _infer_degree_type(self, program_name: str) -> str:
        """Infer degree type from program name."""
        name_lower = program_name.lower()
        if any(term in name_lower for term in ["phd", "ph.d", "doctoral", "doctorate"]):
            return "phd"
        if any(term in name_lower for term in ["mba"]):
            return "master_coursework"
        if any(term in name_lower for term in ["master", "m.s.", "m.a.", "ms ", "ma "]):
            if "research" in name_lower:
                return "master_research"
            return "master_coursework"
        if any(term in name_lower for term in ["bachelor", "b.s.", "b.a.", "undergraduate"]):
            return "bachelor"
        return "master_coursework"

    def _categorize_field(self, field: str | None) -> str | None:
        """Categorize a field of study."""
        if not field:
            return None

        field_lower = field.lower()

        stem_keywords = [
            "computer",
            "engineering",
            "mathematics",
            "physics",
            "chemistry",
            "biology",
            "data science",
            "artificial intelligence",
            "machine learning",
            "statistics",
            "technology",
            "science",
        ]
        if any(kw in field_lower for kw in stem_keywords):
            return "STEM"

        business_keywords = [
            "business",
            "mba",
            "management",
            "finance",
            "accounting",
            "marketing",
            "economics",
            "entrepreneurship",
        ]
        if any(kw in field_lower for kw in business_keywords):
            return "Business"

        arts_keywords = [
            "art",
            "music",
            "design",
            "humanities",
            "philosophy",
            "literature",
            "history",
            "languages",
            "communications",
        ]
        if any(kw in field_lower for kw in arts_keywords):
            return "Arts & Humanities"

        social_keywords = [
            "psychology",
            "sociology",
            "political",
            "international relations",
            "public policy",
            "social work",
            "anthropology",
        ]
        if any(kw in field_lower for kw in social_keywords):
            return "Social Sciences"

        health_keywords = [
            "medicine",
            "nursing",
            "public health",
            "pharmacy",
            "healthcare",
            "medical",
            "biomedical",
        ]
        if any(kw in field_lower for kw in health_keywords):
            return "Health Sciences"

        law_keywords = ["law", "legal", "jurisprudence"]
        if any(kw in field_lower for kw in law_keywords):
            return "Law"

        return "Other"


UNIVERSITY_CONFIGS = {
    "mit": {
        "name": "Massachusetts Institute of Technology",
        "start_urls": ["https://gradadmissions.mit.edu/programs"],
        "program_links_selector": "a.program-link, a[href*='/programs/']",
        "program_name_selector": "h1.program-title::text, h1::text",
        "degree_type_selector": ".degree-type::text",
        "description_selector": ".program-description::text, meta[name='description']::attr(content)",
        "tuition_selector": ".tuition::text, *:contains('Tuition')::text",
        "deadline_selector": ".deadline::text, *:contains('Deadline')::text",
        "duration_selector": ".duration::text",
        "field_selector": ".field-of-study::text",
        "requirements_selector": ".requirements li",
    },
    "stanford": {
        "name": "Stanford University",
        "start_urls": ["https://gradadmissions.stanford.edu/programs"],
        "program_links_selector": "a[href*='program'], a[href*='department']",
        "program_name_selector": "h1::text",
        "degree_type_selector": ".degree::text",
        "description_selector": ".intro::text, .overview::text",
        "tuition_selector": ".cost::text, .tuition::text",
        "deadline_selector": ".deadline::text",
        "duration_selector": ".duration::text",
        "field_selector": ".area::text, .department::text",
        "requirements_selector": ".requirements li, .admission-requirements li",
    },
    "oxford": {
        "name": "University of Oxford",
        "start_urls": ["https://www.ox.ac.uk/admissions/graduate/courses"],
        "program_links_selector": "a[href*='/courses/'], a.course-link",
        "program_name_selector": "h1::text, .course-title::text",
        "degree_type_selector": ".qualification::text",
        "description_selector": ".course-overview::text",
        "tuition_selector": ".fees::text",
        "deadline_selector": ".deadline::text, .application-deadline::text",
        "duration_selector": ".duration::text, .course-length::text",
        "field_selector": ".subject-area::text",
        "requirements_selector": ".entry-requirements li",
    },
}
