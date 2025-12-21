"""
Application Configuration
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Literal
import os


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    # ==================== DATABASE ====================
    DATABASE_URL: str = "postgresql://nqhub:password@localhost:5433/nqhub"
    DATABASE_URL_ASYNC: str = "postgresql+asyncpg://nqhub:password@localhost:5433/nqhub"

    # ==================== REDIS ====================
    REDIS_URL: str = "redis://localhost:6379"

    # ==================== ETL ====================
    ETL_TEMP_DIR: str = "/tmp/nqhub_etl"

    # ==================== NEO4J ====================
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # ==================== SECURITY ====================
    SECRET_KEY: str = "your-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ==================== CORS ====================
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3001", "http://localhost:3000"]

    # ==================== AI / LLM ====================
    # OpenAI
    OPENAI_API_KEY: str | None = None

    # Anthropic
    ANTHROPIC_API_KEY: str | None = None

    # Google AI (Gemini)
    GOOGLE_API_KEY: str | None = None

    # Groq (for Llama)
    GROQ_API_KEY: str | None = None

    # Ollama (for local Llama)
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # mem0
    MEM0_API_KEY: str | None = None

    # ElevenLabs
    ELEVENLABS_API_KEY: str | None = None
    ELEVENLABS_VOICE_ID: str | None = None

    # Default LLM provider
    DEFAULT_LLM_PROVIDER: Literal["openai", "anthropic", "llama"] = "openai"
    DEFAULT_LLM_MODEL: str = "gpt-4-turbo"

    # ==================== EMAIL ====================
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@nqhub.com"

    # ==================== FRONTEND ====================
    FRONTEND_URL: str = "http://localhost:3001"

    # ==================== ENVIRONMENT ====================
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # ==================== SUPERUSER ====================
    SUPERUSER_EMAIL: str = "admin@nqhub.com"
    SUPERUSER_PASSWORD: str = "change-this-password"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


# Create settings instance
settings = Settings()
