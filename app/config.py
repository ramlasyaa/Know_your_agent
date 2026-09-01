import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Know Your Agent - Fraud Detection Layer"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "kya_super_secret_key_change_in_production"

    # Database Settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./kya_dev.db"

    # Risk Scoring Thresholds
    HARD_AMOUNT_LIMIT: float = 1000.00
    VELOCITY_WINDOW_MINUTES: int = 5
    MAX_ACTIONS_PER_WINDOW: int = 5
    ANOMALY_SCORE_THRESHOLD: float = 65.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def async_database_url(self) -> str:
        """Ensure database URL is formatted for async drivers."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
            return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return url


settings = Settings()
