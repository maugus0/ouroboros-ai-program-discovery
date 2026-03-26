"""Tests for HTML parsing utilities."""

from app.crawlers.parsers.html_parser import (
    _detect_degree_type,
    _extract_deadline,
    _extract_tuition,
    extract_basic_metadata,
    extract_page_text,
)


def test_extract_page_text_removes_scripts():
    html = "<html><body><script>var x=1;</script><p>Hello World</p></body></html>"
    text = extract_page_text(html)
    assert "var x" not in text
    assert "Hello World" in text


def test_extract_page_text_removes_nav():
    html = "<html><body><nav>Menu</nav><main>Content</main></body></html>"
    text = extract_page_text(html)
    assert "Menu" not in text
    assert "Content" in text


def test_extract_basic_metadata_title():
    html = "<html><head><title>MSc Data Science</title></head><body><h1>Master of Data Science</h1></body></html>"
    metadata = extract_basic_metadata(html)
    assert metadata["program_name"] == "Master of Data Science"


def test_detect_degree_type_phd():
    assert _detect_degree_type("Apply for our PhD program") == "phd"
    assert _detect_degree_type("Doctoral studies in Engineering") == "phd"


def test_detect_degree_type_master_research():
    assert _detect_degree_type("Master of Science (Research/Thesis)") == "master_research"


def test_detect_degree_type_master_coursework():
    assert _detect_degree_type("Master of Science program") == "master_coursework"


def test_detect_degree_type_bachelor():
    assert _detect_degree_type("Bachelor of Arts in English") == "bachelor"


def test_detect_degree_type_none():
    assert _detect_degree_type("Welcome to our university") is None


def test_extract_deadline_iso():
    assert _extract_deadline("Application deadline: 2026-12-15") == "2026-12-15"


def test_extract_deadline_none():
    assert _extract_deadline("No deadline mentioned here") is None


def test_extract_tuition_usd():
    result = _extract_tuition("Annual tuition: $55,000 per year")
    assert result == 55000.0


def test_extract_tuition_none():
    assert _extract_tuition("Contact admissions for tuition info") is None
