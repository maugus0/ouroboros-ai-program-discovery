"""Application configuration loaded from environment variables."""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_VERSION = "0.1.0"


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
    X_SERVICE_TOKEN: str = ""

    # ========== LLM Configuration ==========
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.1

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    ANTHROPIC_MAX_TOKENS: int = 2000

    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_DELAY: int = 2

    # ========== Crawling Configuration ==========
    SCRAPY_CONCURRENT_REQUESTS: int = 8
    SCRAPY_DOWNLOAD_DELAY: float = 2.0
    SCRAPY_USER_AGENT_ROTATION: bool = True
    MIN_CRAWL_DELAY_SECONDS: int = 2
    MAX_CRAWL_DELAY_SECONDS: int = 5
    RESPECT_ROBOTS_TXT: bool = True

    PROGRAM_STALENESS_DAYS: int = 30
    BATCH_CRAWL_CRON: str = "0 2 * * 0"

    # ========== Ranking Weights (must sum to 100) ==========
    RANKING_WEIGHT_FIELD_RELEVANCE: int = 40
    RANKING_WEIGHT_REQUIREMENT_MATCH: int = 25
    RANKING_WEIGHT_UNIVERSITY_RANKING: int = 15
    RANKING_WEIGHT_DEADLINE_PROXIMITY: int = 10
    RANKING_WEIGHT_TUITION_AFFORDABILITY: int = 10

    # ========== Application ==========
    LOG_LEVEL: str = "INFO"
    USE_MOCK_DATA: bool = True
    ALLOW_DB_FAILURE: bool = False

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


settings = Settings()
