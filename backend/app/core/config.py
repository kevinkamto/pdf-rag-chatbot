"""Application settings, loaded from the environment via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly typed application configuration.

    Values are read from environment variables and an optional ``.env`` file.
    Inject this object (via :func:`get_settings`) rather than reading the
    environment directly anywhere else in the codebase.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAI
    openai_api_key: str
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = Field(default=1536, ge=1)

    # Qdrant (external server)
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection_name: str = "pdf_knowledge_base"

    # Storage
    database_url: str = "sqlite:///./data/app.db"
    upload_dir: str = "./data/uploads"

    # Uploads / security
    max_upload_mb: int = Field(default=20, ge=1)
    management_secret: str = "change-me"

    # CORS
    allowed_origins: str = "http://localhost:3000"

    # RAG behaviour
    top_k: int = Field(default=4, ge=1, le=20)
    fallback_contact: str = "our support team at support@example.com"
    use_demo_corpus: bool = True

    # Chunking
    chunk_tokens: int = Field(default=800, ge=1)
    chunk_overlap_tokens: int = Field(default=100, ge=0)

    @field_validator("qdrant_api_key", mode="before")
    @classmethod
    def _blank_to_none(cls, value: object) -> object:
        """Treat a blank QDRANT_API_KEY (common for local servers) as unset."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def _overlap_below_chunk_size(self) -> Self:
        """Overlap must stay below chunk size, or chunking never advances."""
        if self.chunk_overlap_tokens >= self.chunk_tokens:
            raise ValueError(
                "chunk_overlap_tokens must be less than chunk_tokens "
                f"(got overlap={self.chunk_overlap_tokens}, "
                f"size={self.chunk_tokens})"
            )
        return self

    @property
    def allowed_origins_list(self) -> list[str]:
        """CORS origins as a clean list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()  # type: ignore[call-arg]
