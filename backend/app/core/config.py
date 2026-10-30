import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # JWT Authentication & Cryptography
    SECRET_KEY: str = "smart_quiz_super_secret_jwt_key_for_development_replace_in_prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_SECURE: bool = False

    # AI LLM Provider Configuration (OpenAI SDK with Custom Host support)
    # Project direction: always talk to providers through the OpenAI-compatible API
    # (openai lib + custom base_url) so the backend stays portable across hosts
    # (OpenAI, Gemini OpenAI endpoint, Ollama, vLLM, ...).
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL_NAME: str = "gpt-4o-mini"
    # Backup model used automatically when the primary model is slow or fails.
    # Leave empty to disable model-level failover. (e.g. Gemini: "gemini-2.0-flash-lite")
    LLM_FALLBACK_MODEL_NAME: str = ""
    LLM_TIMEOUT_SECONDS: float = 30.0
    # Issue #16 DoD latency budget.
    # AI_TUTOR_TIMEOUT_SECONDS = overall hard ceiling for the whole /explain call (< 3s).
    # AI_TUTOR_MODEL_TIMEOUT_SECONDS = per-model slice: if the primary model does not
    # answer within this slice, we fail over to LLM_FALLBACK_MODEL_NAME, then to the
    # rule-based pedagogical fallback, all inside the overall ceiling.
    AI_TUTOR_TIMEOUT_SECONDS: float = 2.8
    AI_TUTOR_MODEL_TIMEOUT_SECONDS: float = 2.4
    # Cap on tutor output length. Keep high enough to avoid truncating the Vietnamese
    # explanation (which produces invalid JSON), low enough to bound generation time.
    AI_TUTOR_MAX_TOKENS: int = 700

    # Seed script password
    SEED_DEFAULT_PASSWORD: str = "SmartQuiz@123"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
