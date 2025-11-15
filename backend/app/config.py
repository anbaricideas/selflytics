"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Selflytics"
    environment: str = Field(default="dev", description="Environment: dev, staging, prod")
    debug: bool = Field(default=False, description="Debug mode")
    port: int = Field(default=8000, description="Server port")

    # Database
    firestore_database: str = Field(default="(default)", description="Firestore database name")
    gcp_project_id: str = Field(
        default="selflytics-infra",
        description="GCP project ID",
    )
    gcp_region: str = Field(
        default="australia-southeast1",
        description="GCP region",
    )

    # Authentication
    jwt_secret: str = Field(
        default="dev-secret-change-in-production",
        description="JWT secret key",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        description="JWT token expiry in minutes",
    )

    # CSRF Protection
    csrf_secret: str = Field(
        default="dev-csrf-secret-change-in-production",
        description="CSRF token secret key (min 32 characters)",
    )

    # Security
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:8000", "http://localhost:3000"],
        description="CORS allowed origins",
    )

    # Telemetry
    telemetry_backend: Literal["console", "jsonl", "cloudlogging", "disabled"] = Field(
        default="console",
        alias="TELEMETRY",
        description="Telemetry backend: console|jsonl|cloudlogging|disabled",
    )
    telemetry_log_path: str = Field(
        default="./logs",
        description="Directory for JSONL telemetry files",
    )
    telemetry_log_level: str = Field(
        default="INFO",
        description="Logging level for telemetry",
    )
    telemetry_verbose: bool = Field(
        default=False,
        description="Enable verbose telemetry logging",
    )

    @field_validator("telemetry_log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that log level is a valid Python logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            msg = f"telemetry_log_level must be one of {valid_levels}, got {v!r}"
            raise ValueError(msg)
        return v.upper()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance (deprecated - use get_settings() instead)
settings = get_settings()
