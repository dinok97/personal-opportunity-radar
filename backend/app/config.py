from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_provider: Literal["openrouter", "ollama"] = "openrouter"
    openrouter_api_key: str | None = None
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str = "http://localhost:3000"
    openrouter_app_name: str = "Personal Opportunity Radar"
    llm_timeout_seconds: float = 45.0
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_embedding_base_url: str = "http://localhost:11434"
    pgvector_connection_string: str | None = Field(default=None, min_length=1)
    pgvector_table_name: str = Field(default="cv_chunks", pattern=r"^[a-z_][a-z0-9_]*$")
    pgvector_embedding_dimension: int = Field(default=768, gt=0)
    backend_cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
