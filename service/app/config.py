"""Application Configuration Settings"""

from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # MongoDB settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "gridwise_mvp"

    # API settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "GridWise API"
    VERSION: str = "0.1.0"

    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            # Handle string representation of list from .env file
            import json

            parsed = json.loads(v)
            if isinstance(parsed, list):
                return parsed
            return [parsed] if parsed else []
        return v if isinstance(v, list) else []

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


# Create singleton instance
settings = Settings()
