import json
from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Application Settings loaded from environment variables or .env file."""

    # Project metadata
    PROJECT_NAME: str = "Smart Quiz API"
    API_V1_STR: str = "/api/v1"

    # CORS configuration
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            v = [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            try:
                v = json.loads(v)
            except Exception:
                v = [v]
        return [origin.strip().rstrip("/") for origin in v]

    # Database configuration (PostgreSQL / Supabase / Neon)
    DATABASE_URL: str = "postgresql+psycopg2://postgres:admin@localhost:5432/smart_quiz"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Normalize postgres:// and postgresql:// URLs to use psycopg2 with SQLAlchemy 2.1+."""
        if isinstance(v, str):
            url = v.strip()
            for prefix in ("postgres://", "postgresql://"):
                if url.startswith(prefix):
                    return "postgresql+psycopg2://" + url[len(prefix) :]
            return url
        return v

    # JWT Authentication & Cryptography
    SECRET_KEY: str = "smart_quiz_super_secret_jwt_key_for_development_replace_in_prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_SECURE: bool = False

    # AI LLM Provider Configuration (OpenAI SDK with Custom Host support)
    LLM_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    LLM_API_KEY: str = ""
    LLM_MODEL_NAME: str = "gemini-2.5-flash"
    LLM_FALLBACK_MODEL_NAME: str = ""
    LLM_TIMEOUT_SECONDS: float = Field(default=15.0, gt=0)
    AI_TUTOR_TIMEOUT_SECONDS: float = Field(default=15.0, gt=0)
    AI_TUTOR_MODEL_TIMEOUT_SECONDS: float = Field(default=12.0, gt=0)

    # Seed script password
    SEED_DEFAULT_PASSWORD: str = "SmartQuiz@123"

    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
