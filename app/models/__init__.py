"""Pydantic models for the Program Discovery Agent."""

from app.models.common import (
    CrawlJobStatus,
    CrawlJobType,
    DegreeType,
    ErrorResponse,
    HealthResponse,
    InstitutionFocus,
    InstitutionSize,
    InstitutionStatus,
    InstitutionType,
    LLMCallStatus,
    LLMProvider,
    PaginatedResponse,
    ProgramMode,
    RankingSource,
    RequirementType,
    ResearchOutput,
    SuccessResponse,
)
from app.models.crawl_job import (
    CrawlJobBase,
    CrawlJobCreate,
    CrawlJobDB,
    CrawlJobResponse,
    CrawlJobUpdate,
)
from app.models.explainability import (
    ProgramAgentReasoning,
    ProgramDecisionTraceEntry,
    ProgramEvidenceModel,
    ProgramMatchBreakdown,
    ProgramMatchScoresModel,
    RankingBreakdownSummary,
)
from app.models.institution import (
    InstitutionBase,
    InstitutionCreate,
    InstitutionDB,
    InstitutionFromRankingData,
    InstitutionResponse,
    InstitutionSearchRequest,
    InstitutionUpdate,
)
from app.models.institution_ranking import (
    InstitutionRankingBase,
    InstitutionRankingCreate,
    InstitutionRankingDB,
    InstitutionRankingResponse,
    QSRankingIndicators,
    RankingUpsertData,
)
from app.models.program import (
    ProgramBase,
    ProgramCreate,
    ProgramDB,
    ProgramRankingRequest,
    ProgramResponse,
    ProgramSearchRequest,
    ProgramUpdate,
    RankedProgram,
)
from app.models.program_requirement import (
    ProgramRequirementBase,
    ProgramRequirementBatchCreate,
    ProgramRequirementCreate,
    ProgramRequirementDB,
)

__all__ = [
    # Common
    "CrawlJobStatus",
    "CrawlJobType",
    "DegreeType",
    "ErrorResponse",
    "HealthResponse",
    "InstitutionFocus",
    "InstitutionSize",
    "InstitutionStatus",
    "InstitutionType",
    "LLMCallStatus",
    "LLMProvider",
    "PaginatedResponse",
    "ProgramMode",
    "RankingSource",
    "RequirementType",
    "ResearchOutput",
    "SuccessResponse",
    # Institution
    "InstitutionBase",
    "InstitutionCreate",
    "InstitutionDB",
    "InstitutionFromRankingData",
    "InstitutionResponse",
    "InstitutionSearchRequest",
    "InstitutionUpdate",
    # Institution Ranking
    "InstitutionRankingBase",
    "InstitutionRankingCreate",
    "InstitutionRankingDB",
    "InstitutionRankingResponse",
    "QSRankingIndicators",
    "RankingUpsertData",
    # Program
    "ProgramBase",
    "ProgramCreate",
    "ProgramDB",
    "ProgramRankingRequest",
    "ProgramResponse",
    "ProgramSearchRequest",
    "ProgramUpdate",
    "RankedProgram",
    # Program Requirement
    "ProgramRequirementBase",
    "ProgramRequirementBatchCreate",
    "ProgramRequirementCreate",
    "ProgramRequirementDB",
    # Crawl Job
    "CrawlJobBase",
    "CrawlJobCreate",
    "CrawlJobDB",
    "CrawlJobResponse",
    "CrawlJobUpdate",
    # Explainability
    "ProgramAgentReasoning",
    "ProgramDecisionTraceEntry",
    "ProgramEvidenceModel",
    "ProgramMatchBreakdown",
    "ProgramMatchScoresModel",
    "RankingBreakdownSummary",
]
