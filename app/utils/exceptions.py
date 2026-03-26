"""Custom exception classes for the Program Discovery Agent."""


class ProgramDiscoveryBaseError(Exception):
    """Base exception for all Program Discovery Agent errors."""

    def __init__(self, message: str = "An unexpected error occurred", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseError(ProgramDiscoveryBaseError):
    """Raised when a database operation fails."""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message=message, status_code=500)


class NotFoundError(ProgramDiscoveryBaseError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str = "Resource"):
        super().__init__(message=f"{resource} not found", status_code=404)


class ValidationError(ProgramDiscoveryBaseError):
    """Raised when request validation fails beyond Pydantic checks."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message=message, status_code=422)


class ServiceAuthError(ProgramDiscoveryBaseError):
    """Raised when inter-service authentication fails."""

    def __init__(self, message: str = "Service authentication failed"):
        super().__init__(message=message, status_code=401)


class CrawlError(ProgramDiscoveryBaseError):
    """Raised when a web crawl operation fails."""

    def __init__(self, message: str = "Crawl operation failed"):
        super().__init__(message=message, status_code=502)


class LLMExtractionError(ProgramDiscoveryBaseError):
    """Raised when LLM extraction fails after retries."""

    def __init__(self, message: str = "LLM extraction failed"):
        super().__init__(message=message, status_code=502)


class RankingError(ProgramDiscoveryBaseError):
    """Raised when program ranking fails."""

    def __init__(self, message: str = "Program ranking failed"):
        super().__init__(message=message, status_code=500)
