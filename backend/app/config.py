"""Application configuration using Pydantic Settings."""

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
    environment: str = "dev"
    debug: bool = False

    # Database
    firestore_database: str = "(default)"
    gcp_project_id: str = "selflytics-infra"

    # Authentication
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Telemetry
    telemetry_backend: str = "console"


# Global settings instance
settings = Settings()
