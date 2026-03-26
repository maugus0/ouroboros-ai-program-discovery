"""Pydantic schemas for LLM output validation."""

from typing import Optional

from pydantic import BaseModel, Field


class ExtractedProgramData(BaseModel):
    """Structured program data extracted from HTML by the LLM."""

    program_name: Optional[str] = None
    degree_type: Optional[str] = None
    field: Optional[str] = None
    description: Optional[str] = None
    min_gpa: Optional[float] = None
    prerequisites: list[str] = Field(default_factory=list)
    language_requirements: Optional[str] = None
    deadline: Optional[str] = None
    tuition_usd: Optional[float] = None
    duration_years: Optional[float] = None


class ParsedRequirement(BaseModel):
    """A single parsed admission requirement."""

    type: str
    value: str
    is_mandatory: bool = True


class ParsedRequirements(BaseModel):
    """Collection of parsed requirements from LLM."""

    requirements: list[ParsedRequirement] = Field(default_factory=list)


class FieldClassification(BaseModel):
    """Field classification result from LLM."""

    field: str
    field_category: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
