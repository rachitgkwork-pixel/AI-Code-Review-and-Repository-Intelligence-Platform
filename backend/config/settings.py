from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_env: str = "development"
    app_debug: bool = True
    secret_key: str = "change-me-to-a-long-random-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_code_review"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM
    openai_api_key: str = "sk-placeholder"
    openai_api_base: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # Repository indexing
    repos_base_dir: str = "/tmp/ai_code_review_repos"
    max_file_size_kb: int = 500
    chunk_size: int = 512
    chunk_overlap: int = 64

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
