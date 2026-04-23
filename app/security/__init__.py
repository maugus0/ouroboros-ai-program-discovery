"""Security module for Program Discovery Agent.

Provides input sanitization, output validation, and prompt guardrails
for LLM operations.
"""

from app.security.input_sanitizer import sanitize_dict, sanitize_text
from app.security.output_validator import (
    compute_quality_score,
    validate_program_response,
)
from app.security.prompt_guardrails import (
    build_safe_program_qa_prompt,
    build_safe_prompt,
    wrap_institution_context,
    wrap_program_context,
    wrap_student_profile,
    wrap_user_data,
)

__all__ = [
    "sanitize_text",
    "sanitize_dict",
    "validate_program_response",
    "compute_quality_score",
    "wrap_user_data",
    "wrap_program_context",
    "wrap_institution_context",
    "wrap_student_profile",
    "build_safe_prompt",
    "build_safe_program_qa_prompt",
]
