"""Pydantic models for program requirements."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import RequirementType


class ProgramRequirementBase(BaseModel):
    """Base program requirement fields."""

    requirement_type: RequirementType
    requirement_name: str = Field(..., max_length=256)
    requirement_value: str | None = Field(None, max_length=256)
    is_mandatory: bool = True
    description: str | None = None


class ProgramRequirementCreate(ProgramRequirementBase):
    """Request model for creating a program requirement."""

    program_id: str


class ProgramRequirementDB(ProgramRequirementBase):
    """Program requirement as stored in the database."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    program_id: str
    created_at: datetime


class ProgramRequirementBatchCreate(BaseModel):
    """Batch create requirements for a program."""

    program_id: str
    requirements: list[ProgramRequirementBase]
