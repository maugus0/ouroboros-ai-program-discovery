"""Application configuration loaded from environment variables."""

import json
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_VERSION = "0.2.0"


class Settings(BaseSettings):
    """All application settings. Loaded from .env file."""

    # ========== Database ==========
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "ouroboros_program_db"
    DB_USERNAME: str = "root"
    DB_PASSWORD: str = ""

    DB_POOL_SIZE: int = 10
    DB_POOL_NAME: str = "program_discovery_pool"
    DB_CONNECTION_TIMEOUT: int = 20

    # ========== Inter-Service Auth ==========
    INTERNAL_TOKEN_VERIFY_ENABLED: bool = False
    INTERNAL_TOKEN_SIGNING_ALGORITHM: str = "RS256"
    INTERNAL_TOKEN_PUBLIC_KEY: str = ""
    INTERNAL_TOKEN_PUBLIC_KEYS: str = "{}"
    INTERNAL_TOKEN_JWKS_URL: str = ""
    INTERNAL_TOKEN_JWKS_REFRESH_SECONDS: int = 60
    INTERNAL_TOKEN_JWKS_TIMEOUT_SECONDS: int = 2
    INTERNAL_TOKEN_AUDIENCE: str = "ouroboros.program-discovery"
    INTERNAL_TOKEN_ISSUER: str = "ouroboros-orchestrator-internal"

    # ========== LLM Configuration ==========
    # Primary: OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.0

    # Fallback: Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-haiku-4-5-20251001"
    ANTHROPIC_MAX_TOKENS: int = 2000

    # Retry settings
    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_DELAY: int = 2

    # ========== Ranking Weights (must sum to 100) ==========
    RANKING_WEIGHT_FIELD_RELEVANCE: int = 40
    RANKING_WEIGHT_REQUIREMENT_MATCH: int = 25
    RANKING_WEIGHT_UNIVERSITY_RANKING: int = 15
    RANKING_WEIGHT_DEADLINE_PROXIMITY: int = 10
    RANKING_WEIGHT_TUITION_AFFORDABILITY: int = 10

    # ========== Crawling Configuration ==========
    CRAWL_RESPECT_ROBOTS_TXT: bool = True
    CRAWL_RATE_LIMIT_DELAY: float = 2.0
    CRAWL_USER_AGENT: str = "OuroborosCrawler/1.0 (+https://ouroboros.ai/crawler)"
    CRAWL_TIMEOUT_SECONDS: int = 30
    CRAWL_STALE_DAYS: int = 30

    # ========== Application ==========
    LOG_LEVEL: str = "INFO"
    UVICORN_HOST: str = "127.0.0.1"
    UVICORN_PORT: int = 8002
    USE_MOCK_DATA: bool = True
    ALLOW_DB_FAILURE: bool = False

    # ========== Security ==========
    ENABLE_PROMPT_INJECTION_DETECTION: bool = True
    MAX_INPUT_LENGTH: int = 50000

    # ========== Docker ==========
    RUN_STARTUP_SCRIPTS: bool = True
    DOCKER_MYSQL_PORT: int = 3309

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    def get_db_host(self) -> str:
        return os.getenv("MYSQL_HOST", self.DB_HOST)

    def get_db_name(self) -> str:
        return os.getenv("MYSQL_DATABASE", self.DB_NAME)

    def get_db_user(self) -> str:
        return os.getenv("MYSQL_USER", self.DB_USERNAME)

    def get_db_password(self) -> str:
        return os.getenv("MYSQL_PASSWORD", self.DB_PASSWORD)

    def get_db_port(self) -> int:
        val = os.getenv("MYSQL_PORT")
        return int(val) if val is not None else self.DB_PORT

    def get_ranking_weights(self) -> dict[str, int]:
        return {
            "field_relevance": self.RANKING_WEIGHT_FIELD_RELEVANCE,
            "requirement_match": self.RANKING_WEIGHT_REQUIREMENT_MATCH,
            "university_ranking": self.RANKING_WEIGHT_UNIVERSITY_RANKING,
            "deadline_proximity": self.RANKING_WEIGHT_DEADLINE_PROXIMITY,
            "tuition_affordability": self.RANKING_WEIGHT_TUITION_AFFORDABILITY,
        }

    def get_internal_token_public_keys(self) -> dict[str, str]:
        """Parse INTERNAL_TOKEN_PUBLIC_KEYS JSON string into a kid->PEM dict."""
        try:
            parsed = json.loads(self.INTERNAL_TOKEN_PUBLIC_KEYS)
            if isinstance(parsed, dict):
                return {str(key): str(value) for key, value in parsed.items()}
        except (json.JSONDecodeError, TypeError):
            pass
        return {}


settings = Settings()
