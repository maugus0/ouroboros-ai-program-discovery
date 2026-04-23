"""LLMOps tests for fixture PII guard behavior.

Verifies that the PII scanning script correctly identifies
personal information while allowing synthetic test data.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.check_pii import scan_file  # noqa: E402  # pylint: disable=C0413


def test_pii_guard_ignores_synthetic_numeric_fixture_ids(tmp_path):
    """Synthetic IDs in allowed fields should not trigger PII alerts."""
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        """
{
  "id": "123456789",
  "program_id": "123456789012",
  "zip_code": "123456789"
}
""",
        encoding="utf-8",
    )

    findings, errors = scan_file(str(fixture))

    assert not errors
    assert not findings


def test_pii_guard_flags_vn_national_id_in_sensitive_fields(tmp_path):
    """National IDs in sensitive fields should be flagged."""
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        """
{
  "student_name": "Jane Example",
  "national_id": "123456789"
}
""",
        encoding="utf-8",
    )

    findings, errors = scan_file(str(fixture))

    assert not errors
    assert findings == [(4, "VN CCCD/CMND")]


def test_pii_guard_flags_email_addresses(tmp_path):
    """Real-looking email addresses should be flagged."""
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        """
{
  "student_name": "John Doe",
  "email": "john.doe@gmail.com"
}
""",
        encoding="utf-8",
    )

    findings, errors = scan_file(str(fixture))

    assert not errors
    assert len(findings) == 1
    assert findings[0][1] == "Email"


def test_pii_guard_flags_us_phone_numbers(tmp_path):
    """US phone numbers should be flagged."""
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        """
{
  "contact": "+1-555-123-4567"
}
""",
        encoding="utf-8",
    )

    findings, errors = scan_file(str(fixture))

    assert not errors
    assert len(findings) == 1
    assert findings[0][1] == "US Phone"


def test_pii_guard_flags_ssn(tmp_path):
    """US Social Security Numbers should be flagged."""
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        """
{
  "ssn": "123-45-6789"
}
""",
        encoding="utf-8",
    )

    findings, errors = scan_file(str(fixture))

    assert not errors
    assert len(findings) == 1
    assert findings[0][1] == "US SSN"


def test_pii_guard_allows_synthetic_test_data(tmp_path):
    """Synthetic test data with fake values should pass."""
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        """
{
  "student_name": "Test Student",
  "university": "Test University",
  "gpa": 3.85,
  "program_id": "prog_12345",
  "preferences": {
    "country": "United States",
    "field": "Computer Science"
  }
}
""",
        encoding="utf-8",
    )

    findings, errors = scan_file(str(fixture))

    assert not errors
    assert not findings


def test_pii_guard_handles_empty_file(tmp_path):
    """Empty files should not cause errors."""
    fixture = tmp_path / "empty.json"
    fixture.write_text("{}", encoding="utf-8")

    findings, errors = scan_file(str(fixture))

    assert not errors
    assert not findings
