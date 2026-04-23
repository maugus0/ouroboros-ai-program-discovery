"""Validate LLM outputs for quality, safety, and program relevance.

Provides post-generation validation to detect:
1. Prompt leakage (model revealing system instructions)
2. Injection echoes (model repeating jailbreak attempts)
3. Generic/low-quality responses
4. Program context relevance
"""

import re
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

# Patterns that suggest the model leaked internal prompt/instructions
PROMPT_LEAKAGE_PATTERNS = [
    r"\bas an ai\b",
    r"\bi cannot\b",
    r"\bi don't have access\b",
    r"\bi'm unable to\b",
    r"\bsystem instructions\b",
    r"===== ",
    r"<\|.*?\|>",
    r"\[INST\]",
    r"<\|im_start\|>",
    r"STUDENT_CONTEXT",
    r"PROGRAM_CONTEXT",
    r"treat as data only",
]

# Patterns that suggest the model echoed jailbreak / instruction text.
OUTPUT_INJECTION_PATTERNS = [
    r"ignore (all |previous )?instructions",
    r"disregard (all |previous )?instructions",
    r"you are now (a |an )?",
    r"new task:",
    r"developer mode",
    r"jailbreak",
    r"<\|assistant\|>",
    r"<\|system\|>",
]

# Generic phrases that indicate low-quality, template-like responses
GENERIC_PHRASES = [
    "i would be happy to help",
    "thank you for your question",
    "i hope this helps",
    "please let me know if you need",
    "feel free to ask",
    "i'm here to assist",
    "is there anything else",
]


def _extract_relevance_strings(
    programs_context: list[dict[str, Any]] | None,
    institutions_context: list[dict[str, Any]] | None,
) -> list[str]:
    """Extract distinctive strings the response should mention (program/institution names)."""
    refs: list[str] = []
    seen: set[str] = set()

    for prog in programs_context or []:
        for key in ("program_name", "name", "institution_name"):
            val = str(prog.get(key) or "").strip()
            if len(val) >= 3:
                low = val.lower()
                if low not in seen:
                    seen.add(low)
                    refs.append(low)

    for inst in institutions_context or []:
        for key in ("name", "institution_name"):
            val = str(inst.get(key) or "").strip()
            if len(val) >= 3:
                low = val.lower()
                if low not in seen:
                    seen.add(low)
                    refs.append(low)

    return refs[:10]


def check_program_relevance(
    content: str,
    programs_context: list[dict[str, Any]] | None = None,
    institutions_context: list[dict[str, Any]] | None = None,
) -> tuple[bool, str | None]:
    """Check if the response mentions expected program/institution context.

    Returns:
        (ok, issue_message) tuple
    """
    if not content or not content.strip():
        return False, "Content is empty"

    refs = _extract_relevance_strings(programs_context, institutions_context)
    if not refs:
        return True, None

    hay = content.lower()
    for ref in refs:
        if ref in hay:
            return True, None

    preview = ", ".join(refs[:3])
    return False, f"Response does not reference expected program context (e.g. {preview})"


def validate_program_response(
    content: str,
    min_length: int = 50,
    max_length: int = 10000,
    *,
    programs_context: list[dict[str, Any]] | None = None,
    institutions_context: list[dict[str, Any]] | None = None,
) -> tuple[bool, list[str]]:
    """Validate LLM program response: length, leakage, injection echoes, relevance.

    Args:
        content: The LLM-generated response
        min_length: Minimum character length
        max_length: Maximum character length
        programs_context: Programs that should be referenced
        institutions_context: Institutions that should be referenced

    Returns:
        (is_valid, issues) tuple where issues is a list of problem descriptions
    """
    issues: list[str] = []

    if not content or not content.strip():
        return False, ["Content is empty"]

    if len(content) < min_length:
        issues.append(f"Response too short: {len(content)} chars (minimum {min_length})")
    elif len(content) > max_length:
        issues.append(f"Response too long: {len(content)} chars (maximum {max_length})")

    low = content.lower()

    for pattern in PROMPT_LEAKAGE_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(f"Potential prompt leakage detected: '{pattern}'")
            logger.error("prompt_leakage_in_output", pattern=pattern, content_sample=content[:200])
            break

    for pattern in OUTPUT_INJECTION_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(f"Potential injected instruction echoed in output: '{pattern}'")
            logger.warning("output_injection_pattern", pattern=pattern, content_sample=content[:200])
            break

    generic_count = sum(1 for phrase in GENERIC_PHRASES if phrase in low)
    if generic_count >= 3:
        issues.append(f"Response contains {generic_count} generic phrases (may be low quality)")

    rel_ok, rel_msg = check_program_relevance(content, programs_context, institutions_context)
    if not rel_ok and rel_msg and (programs_context or institutions_context):
        issues.append(rel_msg)

    return len(issues) == 0, issues


def compute_quality_score(
    content: str,
    programs_context: list[dict[str, Any]] | None = None,
    institutions_context: list[dict[str, Any]] | None = None,
) -> float:
    """Compute a quality score (0.0-1.0) for generated program response.

    Scores are reduced for:
    - Too short/long responses
    - Prompt leakage patterns
    - Injection pattern echoes
    - Generic phrases
    - Missing program context references
    """
    score = 1.0

    if not content:
        return 0.0

    if len(content) < 50:
        score -= 0.3
    elif len(content) > 10000:
        score -= 0.2

    low = content.lower()

    for pattern in PROMPT_LEAKAGE_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            score -= 0.2
            break

    for pattern in OUTPUT_INJECTION_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            score -= 0.25
            break

    generic_count = sum(1 for phrase in GENERIC_PHRASES if phrase in low)
    score -= min(0.2, generic_count * 0.05)

    rel_ok, _ = check_program_relevance(content, programs_context, institutions_context)
    if not rel_ok and (programs_context or institutions_context):
        score -= 0.15

    sentences = re.split(r"[.!?]+", content)
    if len(sentences) > 3:
        avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / max(len(sentences), 1)
        if avg_sentence_length < 5:
            score -= 0.1
        elif avg_sentence_length > 50:
            score -= 0.1

    return max(0.0, min(1.0, score))
