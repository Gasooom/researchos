"""Application configuration for ResearchOS."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    tavily_api_key: str | None = Field(
        default=None,
        alias="TAVILY_API_KEY",
    )

    openai_api_key: str | None = Field(
        default=None,
        alias="OPENAI_API_KEY",
    )

    llm_model: str = Field(
        default="gpt-5-mini",
        alias="LLM_MODEL",
    )

    llm_mode: str = Field(
        default="deterministic",
        alias="LLM_MODE",
    )

    research_database_path: str = Field(
        default="researchos.db",
        alias="RESEARCH_DATABASE_PATH",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()


def get_environment() -> str:
    """Return the configured application environment."""
    return get_settings().app_env


def get_log_level() -> str:
    """Return the configured logging level."""
    return get_settings().log_level
