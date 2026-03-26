"""BeautifulSoup helpers for extracting program data from HTML pages."""

import re
from typing import Any, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.core.logging import get_logger
from app.utils.html_utils import clean_html_text

logger = get_logger(__name__)


def extract_page_text(html: str) -> str:
    """Extract and clean readable text from raw HTML."""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    return clean_html_text(text)


def extract_basic_metadata(html: str) -> dict[str, Any]:
    """Regex-based fallback extraction when LLM is unavailable.

    Attempts to find common patterns for program pages without LLM assistance.
    """
    soup = BeautifulSoup(html, "lxml")
    result: dict[str, Any] = {
        "program_name": None,
        "degree_type": None,
        "field": None,
        "description": None,
        "deadline": None,
        "tuition_usd": None,
    }

    title_tag = soup.find("title")
    if title_tag:
        result["program_name"] = clean_html_text(title_tag.get_text())

    h1_tag = soup.find("h1")
    if h1_tag:
        result["program_name"] = clean_html_text(h1_tag.get_text())

    result["degree_type"] = _detect_degree_type(html)

    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        result["description"] = meta_desc["content"][:500]

    result["deadline"] = _extract_deadline(html)
    result["tuition_usd"] = _extract_tuition(html)

    return result


def program_page_metadata(html: str, source_url: str, **extra: Any) -> dict[str, Any]:
    """Build basic program metadata dict with ``source_url`` and optional spider fields."""
    metadata = extract_basic_metadata(html)
    metadata["source_url"] = source_url
    metadata.update(extra)
    return metadata


def extract_links(html: str, base_url: str) -> list[str]:
    """Extract all links from a page that might lead to program detail pages."""
    soup = BeautifulSoup(html, "lxml")
    links = []

    program_keywords = ["program", "course", "degree", "master", "phd", "bachelor", "graduate", "admission"]

    for anchor in soup.find_all("a", href=True):
        raw_href = anchor.get("href")
        if not raw_href or not isinstance(raw_href, str):
            continue
        href = raw_href.strip()
        text = anchor.get_text(strip=True).lower()

        if any(kw in href.lower() or kw in text for kw in program_keywords):
            if href.startswith("/"):
                href = urljoin(base_url, href)
            if href.startswith("http"):
                links.append(href)

    return list(set(links))


def _detect_degree_type(html: str) -> Optional[str]:
    """Detect degree type from page content."""
    text = html.lower()
    if "ph.d" in text or "phd" in text or "doctorate" in text or "doctoral" in text:
        return "phd"
    if "master" in text and ("research" in text or "thesis" in text):
        return "master_research"
    if "master" in text or "m.s." in text or "m.a." in text or "msc" in text:
        return "master_coursework"
    if "bachelor" in text or "b.s." in text or "b.a." in text or "undergraduate" in text:
        return "bachelor"
    return None


def _extract_deadline(html: str) -> Optional[str]:
    """Attempt to extract application deadlines using regex patterns."""
    date_patterns = [
        r"deadline[:\s]*(\w+\s+\d{1,2},?\s+\d{4})",
        r"apply\s+by[:\s]*(\w+\s+\d{1,2},?\s+\d{4})",
        r"(\d{4}-\d{2}-\d{2})",
    ]
    for pattern in date_patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def _extract_tuition(html: str) -> Optional[float]:
    """Attempt to extract tuition amounts using regex patterns."""
    patterns = [
        r"\$\s?([\d,]+(?:\.\d{2})?)\s*(?:per\s+year|annually|/year)",
        r"tuition[:\s]*\$\s?([\d,]+(?:\.\d{2})?)",
        r"USD\s?([\d,]+(?:\.\d{2})?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                continue
    return None
