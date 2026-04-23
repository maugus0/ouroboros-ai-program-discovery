"""Input sanitization to prevent prompt injection and malicious content.

Provides defense-in-depth against prompt injection attacks by:
1. Stripping Unicode control characters
2. Detecting instruction-like patterns used in jailbreaks
3. Enforcing length limits
4. Recursive sanitization of nested data structures
"""

import re
import unicodedata
from typing import Any

from app.config import settings
from app.core.logging import get_logger
from app.utils.exceptions import PromptInjectionError, ValidationError

logger = get_logger(__name__)

# Instruction-like substrings commonly used in jailbreaks (case-insensitive match).
CONTROL_PATTERNS = [
    r"<\|.*?\|>",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"\[\s*INST\s*\]",
    r"\[/INST\]",
    r"###\s*SYSTEM",
    r"###\s*ASSISTANT",
    r"###\s*USER",
    r"###\s*IGNORE",
    r"IGNORE\s+(PREVIOUS|ALL)\s+INSTRUCTIONS",
    r"DISREGARD\s+(PREVIOUS|ALL)\s+INSTRUCTIONS",
    r"OVERRIDE\s+SYSTEM",
    r"NEW\s+INSTRUCTIONS?\s*:",
    r"BEGIN\s+SYSTEM\s+PROMPT",
    r"END\s+SYSTEM\s+PROMPT",
    r"<\s*script",
    r"</\s*script\s*>",
    r"DEVELOPER\s+MODE",
    r"JAILBREAK",
    r"YOU\s+ARE\s+NOW",
    r"<\|assistant\|>",
    r"<\|system\|>",
]

MAX_INPUT_LENGTH = 50000


def strip_control_characters(text: str, *, preserve_newline_tab: bool = True) -> str:
    """Remove Unicode control characters (category ``Cc``).

    Optionally keeps ``\\n`` and ``\\t`` so multi-line text stays readable; other
    ``Cc`` (NUL, bells, escape, etc.) are stripped.
    """
    if not text:
        return text
    out: list[str] = []
    for ch in text:
        if preserve_newline_tab and ch in "\n\t":
            out.append(ch)
            continue
        if unicodedata.category(ch) == "Cc":
            continue
        out.append(ch)
    return "".join(out)


def check_prompt_injection(text: str, field_name: str = "input") -> None:
    """Check for prompt injection patterns and raise if detected.

    Args:
        text: Text to check
        field_name: Field name for logging

    Raises:
        PromptInjectionError: If control instructions are detected
    """
    for pattern in CONTROL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(
                "potential_prompt_injection_detected",
                field=field_name,
                pattern=pattern,
                text_sample=text[:200],
            )
            raise PromptInjectionError(f"{field_name} contains suspicious patterns that may attempt prompt injection")


def sanitize_text(text: str, field_name: str = "input") -> str:
    """Sanitize text input.

    Args:
        text: Raw text from user
        field_name: Field name for logging

    Returns:
        Cleaned text

    Raises:
        ValidationError: If input is too long
        PromptInjectionError: If control instructions are detected
    """
    if not text:
        return text

    text = strip_control_characters(text)

    if len(text) > MAX_INPUT_LENGTH:
        raise ValidationError(f"{field_name} exceeds maximum length of {MAX_INPUT_LENGTH} characters")

    text = re.sub(r"[\t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" +", " ", text).strip()

    enable_detection = getattr(settings, "ENABLE_PROMPT_INJECTION_DETECTION", True)
    if enable_detection:
        check_prompt_injection(text, field_name)

    return text


def sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively sanitize all text fields in a dictionary.

    Args:
        data: Dictionary potentially containing user input

    Returns:
        Sanitized dictionary with all string values cleaned
    """
    sanitized: dict[str, Any] = {}

    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_text(value, field_name=key)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [_sanitize_list_item(item, key) for item in value]
        else:
            sanitized[key] = value

    return sanitized


def _sanitize_list_item(item: Any, field_name: str) -> Any:
    """Sanitize a single list item."""
    if isinstance(item, str):
        return sanitize_text(item, field_name=field_name)
    if isinstance(item, dict):
        return sanitize_dict(item)
    return item
