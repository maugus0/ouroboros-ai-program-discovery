"""Common Pydantic models and enums shared across the application."""

from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class InstitutionType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    PRIVATE_NOT_FOR_PROFIT = "private_not_for_profit"
    UNKNOWN = "unknown"


class InstitutionSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"
    UNKNOWN = "unknown"


class InstitutionFocus(str, Enum):
    FULL_COMPREHENSIVE = "full_comprehensive"
    FOCUSED = "focused"
    SPECIALIST = "specialist"
    UNKNOWN = "unknown"


class ResearchOutput(str, Enum):
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"
    UNKNOWN = "unknown"


class InstitutionStatus(str, Enum):
    VERIFIED = "verified"
    PENDING = "pending"
    REJECTED = "rejected"


class RankingSource(str, Enum):
    QS_WORLD = "qs_world"
    TIMES_HIGHER = "times_higher"
    ARWU = "arwu"
    US_NEWS = "us_news"
    WEBOMETRICS = "webometrics"
    CWUR = "cwur"
    OTHER = "other"


class DegreeType(str, Enum):
    BACHELORS = "bachelors"
    MASTERS = "masters"
    PHD = "phd"
    DIPLOMA = "diploma"
    CERTIFICATE = "certificate"
    OTHER = "other"


class ProgramMode(str, Enum):
    ON_CAMPUS = "on_campus"
    ONLINE = "online"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"


class RequirementType(str, Enum):
    GPA = "gpa"
    GRE = "gre"
    GMAT = "gmat"
    TOEFL = "toefl"
    IELTS = "ielts"
    DUOLINGO = "duolingo"
    SAT = "sat"
    ACT = "act"
    WORK_EXPERIENCE = "work_experience"
    DEGREE = "degree"
    PORTFOLIO = "portfolio"
    INTERVIEW = "interview"
    ESSAY = "essay"
    RECOMMENDATION = "recommendation"
    OTHER = "other"


class CrawlJobType(str, Enum):
    INSTITUTION_RANKING = "institution_ranking"
    PROGRAM_LIST = "program_list"
    PROGRAM_DETAIL = "program_detail"
    FULL_SYNC = "full_sync"


class CrawlJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OTHER = "other"


class LLMCallStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class SuccessResponse(BaseModel):
    """Standard success response."""

    success: bool = True
    message: str = "Operation completed successfully"


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = False
    message: str
    details: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    database: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
