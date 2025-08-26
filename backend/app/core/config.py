import urllib.parse
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "WeatherAI"
    env: str = Field(default="dev", alias="ENV")
    debug: bool = Field(default=True)

    # Database - PostgreSQL
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="WeatherAI", alias="POSTGRES_DB")
    postgres_user: str = Field(default="weatherai", alias="POSTGRES_USER")
    postgres_password: str = Field(default="Your_password123", alias="POSTGRES_PASSWORD")

    # Redis
    redis_url: str = Field(default="redis://redis:6379", alias="REDIS_URL")

    # JWT
    jwt_secret: str = Field(default="change-this-secret-key", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    # OpenAI (Legacy - keeping for backward compatibility)
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", alias="OPENAI_MODEL")

    # Azure OpenAI
    azure_openai_endpoint: str | None = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str | None = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_embedding_deployment: str | None = Field(default=None, alias="AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    azure_openai_embedding_dim: int = Field(default=1536, alias="AZURE_OPENAI_EMBEDDING_DIM")
    azure_openai_chat_deployment: str | None = Field(default=None, alias="AZURE_OPENAI_CHAT_DEPLOYMENT")

    # Logging & Debug
    sqlalchemy_echo: bool = Field(default=False, alias="SQLALCHEMY_ECHO")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Metrics
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")

    # Weather Data Ingestion
    openmeteo_base_url: str = Field(default="https://api.open-meteo.com", alias="OPENMETEO_BASE_URL")
    enable_metar: bool = Field(default=False, alias="ENABLE_METAR")
    metar_base_url: str = Field(default="https://aviationweather.gov/adds/dataserver_current/httpparam", alias="METAR_BASE_URL")
    ingest_interval_minutes: int = Field(default=120, alias="INGEST_INTERVAL_MINUTES")
    max_locations_per_ingest: int = Field(default=25, alias="MAX_LOCATIONS_PER_INGEST")
    disable_ingest_in_dev: bool = Field(default=True, alias="DISABLE_INGEST_IN_DEV")
    openmeteo_air_quality_strict: bool = Field(default=False, alias="OPENMETEO_AIR_QUALITY_STRICT")

    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=60, alias="RATE_LIMIT_REQUESTS_PER_MINUTE")
    llm_rate_limit_requests_per_minute: int = Field(default=10, alias="LLM_RATE_LIMIT_REQUESTS_PER_MINUTE")

    # Digest Settings
    digest_cache_ttl_seconds: int = Field(default=600, alias="DIGEST_CACHE_TTL_SECONDS")
    digest_use_llm: bool = Field(default=True, alias="DIGEST_USE_LLM")

    # RAG Defaults (Phase 4 requirements)
    rag_chunk_size: int = Field(default=512, alias="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(default=50, alias="RAG_CHUNK_OVERLAP")
    rag_similarity_threshold: float = Field(default=0.55, alias="RAG_SIMILARITY_THRESHOLD")  # Phase 4: lowered from 0.75
    rag_top_k: int = Field(default=8, alias="RAG_TOP_K")  # Phase 4: increased max to 8
    rag_mmr_lambda: float = Field(default=0.5, alias="RAG_MMR_LAMBDA")  # Phase 4: relevance weight
    rag_answer_cache_ttl_seconds: int = Field(default=3600, alias="RAG_ANSWER_CACHE_TTL_SECONDS")  # Phase 4: 1h instead of 6h
    rag_embedding_cache_ttl_seconds: int = Field(default=604800, alias="RAG_EMBEDDING_CACHE_TTL_SECONDS")  # Phase 4: 7d for embeddings
    rag_enable_mmr: bool = Field(default=True, alias="RAG_ENABLE_MMR")  # Phase 4: optional MMR toggle
    rag_max_query_length: int = Field(default=2000, alias="RAG_MAX_QUERY_LENGTH")  # Phase 4: input validation
    rag_stream_rate_limit: int = Field(default=20, alias="RAG_STREAM_RATE_LIMIT")  # Phase 4: 20 requests per 5 min
    rag_stream_rate_window_seconds: int = Field(default=300, alias="RAG_STREAM_RATE_WINDOW_SECONDS")  # Phase 4: 5 min window

    # Analytics
    analytics_max_range_days: int = Field(default=30, alias="ANALYTICS_MAX_RANGE_DAYS")

    # Redis Cache Configuration
    use_redis_rate_limit: bool = Field(default=True, alias="USE_REDIS_RATE_LIMIT")
    redis_cache_analytics_ttl: int = Field(default=60, alias="REDIS_CACHE_ANALYTICS_TTL")
    redis_cache_forecast_ttl: int = Field(default=300, alias="REDIS_CACHE_FORECAST_TTL")

    # Analytics Pipeline
    no_refresh: bool = Field(default=False, alias="NO_REFRESH")

    # Observability Settings (Phase 5)
    environment: str = Field(default="development", alias="ENVIRONMENT")
    otlp_endpoint: str | None = Field(default=None, alias="OTLP_ENDPOINT")
    enable_prometheus_metrics: bool = Field(default=True, alias="ENABLE_PROMETHEUS_METRICS")
    metrics_auth_token: str | None = Field(default=None, alias="METRICS_AUTH_TOKEN")
    json_logs: bool = Field(default=True, alias="JSON_LOGS")
    
    # Tracing settings
    enable_tracing: bool = Field(default=True, alias="ENABLE_TRACING")
    trace_sample_rate: float = Field(default=1.0, alias="TRACE_SAMPLE_RATE")  # 1.0 = 100% sampling
    
    # Token/Cost tracking
    enable_cost_tracking: bool = Field(default=True, alias="ENABLE_COST_TRACKING")
    cost_tracking_sampling_rate: float = Field(default=1.0, alias="COST_TRACKING_SAMPLING_RATE")

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:5173", "http://127.0.0.1:5173"], alias="CORS_ORIGINS")

    # Database Bootstrap
    skip_db_bootstrap: bool = Field(default=False, alias="SKIP_DB_BOOTSTRAP")
    db_bootstrap_max_attempts: int = Field(default=30, alias="DB_BOOTSTRAP_MAX_ATTEMPTS")
    db_bootstrap_sleep_seconds: int = Field(default=2, alias="DB_BOOTSTRAP_SLEEP_SECONDS")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields to be ignored

    @field_validator("azure_openai_embedding_dim")
    @classmethod
    def validate_embedding_dim(cls, v: int) -> int:
        """Ensure embedding dimension is positive."""
        if v <= 0:
            raise ValueError("azure_openai_embedding_dim must be positive")
        return v

    @model_validator(mode='after')
    def validate_chunk_settings(self) -> 'AppSettings':
        """Validate RAG chunk settings."""
        if self.rag_chunk_overlap >= self.rag_chunk_size:
            raise ValueError("rag_chunk_overlap must be less than rag_chunk_size")
        return self

    def model_post_init(self, __context) -> None:
        """Post-initialization validation."""
        # Apply CORS parsing
        if isinstance(self.cors_origins, str):
            self.cors_origins = self.parse_cors_origins(self.cors_origins)

    @property
    def database_url(self) -> str:
        """Build PostgreSQL connection string for SQLAlchemy async."""
        password_encoded = urllib.parse.quote_plus(self.postgres_password)
        return f"postgresql+psycopg://{self.postgres_user}:{password_encoded}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def database_url_sync(self) -> str:
        """Build PostgreSQL connection string for SQLAlchemy sync (for migrations)."""
        password_encoded = urllib.parse.quote_plus(self.postgres_password)
        return f"postgresql+psycopg://{self.postgres_user}:{password_encoded}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from environment variable (comma-separated or list)."""
        if isinstance(v, str):
            # Parse comma-separated string
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            # Add fallback origins if not present
            fallback_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
            for fallback in fallback_origins:
                if fallback not in origins:
                    origins.append(fallback)
            return origins
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    def __init__(self, **data):
        super().__init__(**data)
        # Apply CORS parsing
        if isinstance(self.cors_origins, str):
            self.cors_origins = self.parse_cors_origins(self.cors_origins)


def load_secrets_from_key_vault(settings: AppSettings) -> None:
    """
    Load secrets from Azure Key Vault.
    
    TODO: Implement actual Key Vault integration when needed.
    This is a placeholder for future secret management implementation.
    
    Args:
        settings: The settings object to potentially update with vault secrets
    """
    # Placeholder implementation - no-op for now
    pass


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """
    Get memoized singleton settings instance.
    
    Returns:
        AppSettings: The singleton settings instance
    """
    settings = AppSettings()
    load_secrets_from_key_vault(settings)
    return settings


# Global settings instance for backward compatibility
# New code should use get_settings() instead
settings = AppSettings()
