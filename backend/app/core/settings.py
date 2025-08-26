"""Centralized settings management for WeatherAI.

This module provides typed configuration sections and centralized
settings loading for all application components.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    dialect: str = Field(default="postgres", alias="DB_DIALECT")
    host: str = Field(default="localhost", alias="POSTGRES_HOST")
    port: int = Field(default=5432, alias="POSTGRES_PORT")
    name: str = Field(default="WeatherAI", alias="POSTGRES_DB")
    user: str = Field(default="weatherai", alias="POSTGRES_USER")
    password: str = Field(default="Your_password123", alias="POSTGRES_PASSWORD")

    @property
    def url(self) -> str:
        """Get SQLAlchemy database URL."""
        import urllib.parse
        password_encoded = urllib.parse.quote_plus(self.password)
        return f"postgresql+psycopg://{self.user}:{password_encoded}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""

    url: str = Field(default="redis://redis:6379", alias="REDIS_URL")
    max_connections: int = Field(default=20, alias="REDIS_MAX_CONNECTIONS")
    socket_timeout: int = Field(default=5, alias="REDIS_SOCKET_TIMEOUT")


class OpenAISettings(BaseSettings):
    """OpenAI API configuration settings."""

    # OpenAI (Legacy - keeping for backward compatibility)
    api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    model: str = Field(default="gpt-4", alias="OPENAI_MODEL")
    max_tokens: int = Field(default=2000, alias="OPENAI_MAX_TOKENS")
    temperature: float = Field(default=0.1, alias="OPENAI_TEMPERATURE")
    timeout: int = Field(default=30, alias="OPENAI_TIMEOUT_SECONDS")

    # Azure OpenAI
    azure_endpoint: str | None = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_api_key: str | None = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_embedding_deployment: str | None = Field(default=None, alias="AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    azure_embedding_dim: int = Field(default=1536, alias="AZURE_OPENAI_EMBEDDING_DIM")
    azure_chat_deployment: str | None = Field(default=None, alias="AZURE_OPENAI_CHAT_DEPLOYMENT")

    @field_validator("azure_embedding_dim")
    @classmethod
    def validate_embedding_dim(cls, v: int) -> int:
        """Ensure embedding dimension is positive."""
        if v <= 0:
            raise ValueError("azure_openai_embedding_dim must be positive")
        return v


class SecuritySettings(BaseSettings):
    """Security and authentication settings."""

    jwt_secret: str = Field(default="change-this-secret-key", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        alias="CORS_ORIGINS"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
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


class FeatureFlags(BaseSettings):
    """Feature flags for enabling/disabling functionality."""

    enable_rag: bool = Field(default=True, alias="FEATURE_ENABLE_RAG")
    enable_analytics: bool = Field(default=True, alias="FEATURE_ENABLE_ANALYTICS")
    enable_caching: bool = Field(default=True, alias="FEATURE_ENABLE_CACHING")
    enable_rate_limiting: bool = Field(default=True, alias="FEATURE_ENABLE_RATE_LIMITING")
    
    # Ingestion settings
    disable_ingest_in_dev: bool = Field(default=True, alias="DISABLE_INGEST_IN_DEV")
    enable_metar: bool = Field(default=False, alias="ENABLE_METAR")
    
    # Observability settings
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")
    enable_prometheus_metrics: bool = Field(default=True, alias="ENABLE_PROMETHEUS_METRICS")
    enable_tracing: bool = Field(default=True, alias="ENABLE_TRACING")
    enable_cost_tracking: bool = Field(default=True, alias="ENABLE_COST_TRACKING")
    json_logs: bool = Field(default=True, alias="JSON_LOGS")


class WeatherDataSettings(BaseSettings):
    """Weather data ingestion configuration."""
    
    openmeteo_base_url: str = Field(default="https://api.open-meteo.com", alias="OPENMETEO_BASE_URL")
    metar_base_url: str = Field(default="https://aviationweather.gov/adds/dataserver_current/httpparam", alias="METAR_BASE_URL")
    ingest_interval_minutes: int = Field(default=120, alias="INGEST_INTERVAL_MINUTES")
    max_locations_per_ingest: int = Field(default=25, alias="MAX_LOCATIONS_PER_INGEST")
    openmeteo_air_quality_strict: bool = Field(default=False, alias="OPENMETEO_AIR_QUALITY_STRICT")


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration."""
    
    requests_per_minute: int = Field(default=60, alias="RATE_LIMIT_REQUESTS_PER_MINUTE")
    llm_requests_per_minute: int = Field(default=10, alias="LLM_RATE_LIMIT_REQUESTS_PER_MINUTE")
    use_redis_rate_limit: bool = Field(default=True, alias="USE_REDIS_RATE_LIMIT")


class CacheSettings(BaseSettings):
    """Cache configuration settings."""
    
    digest_cache_ttl_seconds: int = Field(default=600, alias="DIGEST_CACHE_TTL_SECONDS")
    redis_cache_analytics_ttl: int = Field(default=60, alias="REDIS_CACHE_ANALYTICS_TTL")
    redis_cache_forecast_ttl: int = Field(default=300, alias="REDIS_CACHE_FORECAST_TTL")


class RAGSettings(BaseSettings):
    """RAG (Retrieval Augmented Generation) configuration."""
    
    chunk_size: int = Field(default=512, alias="RAG_CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, alias="RAG_CHUNK_OVERLAP")
    similarity_threshold: float = Field(default=0.55, alias="RAG_SIMILARITY_THRESHOLD")
    top_k: int = Field(default=8, alias="RAG_TOP_K")
    mmr_lambda: float = Field(default=0.5, alias="RAG_MMR_LAMBDA")
    answer_cache_ttl_seconds: int = Field(default=3600, alias="RAG_ANSWER_CACHE_TTL_SECONDS")
    embedding_cache_ttl_seconds: int = Field(default=604800, alias="RAG_EMBEDDING_CACHE_TTL_SECONDS")
    enable_mmr: bool = Field(default=True, alias="RAG_ENABLE_MMR")
    max_query_length: int = Field(default=2000, alias="RAG_MAX_QUERY_LENGTH")
    stream_rate_limit: int = Field(default=20, alias="RAG_STREAM_RATE_LIMIT")
    stream_rate_window_seconds: int = Field(default=300, alias="RAG_STREAM_RATE_WINDOW_SECONDS")

    @model_validator(mode='after')
    def validate_chunk_settings(self) -> 'RAGSettings':
        """Validate RAG chunk settings."""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return self


class ObservabilitySettings(BaseSettings):
    """Observability and monitoring configuration."""
    
    environment: str = Field(default="development", alias="ENVIRONMENT")
    otlp_endpoint: str | None = Field(default=None, alias="OTLP_ENDPOINT")
    metrics_auth_token: str | None = Field(default=None, alias="METRICS_AUTH_TOKEN")
    trace_sample_rate: float = Field(default=1.0, alias="TRACE_SAMPLE_RATE")
    cost_tracking_sampling_rate: float = Field(default=1.0, alias="COST_TRACKING_SAMPLING_RATE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    sqlalchemy_echo: bool = Field(default=False, alias="SQLALCHEMY_ECHO")


class AnalyticsSettings(BaseSettings):
    """Analytics pipeline configuration."""
    
    max_range_days: int = Field(default=30, alias="ANALYTICS_MAX_RANGE_DAYS")
    no_refresh: bool = Field(default=False, alias="NO_REFRESH")


class DigestSettings(BaseSettings):
    """Digest generation configuration."""
    
    use_llm: bool = Field(default=True, alias="DIGEST_USE_LLM")


class DatabaseBootstrapSettings(BaseSettings):
    """Database bootstrap configuration."""
    
    skip_db_bootstrap: bool = Field(default=False, alias="SKIP_DB_BOOTSTRAP")
    db_bootstrap_max_attempts: int = Field(default=30, alias="DB_BOOTSTRAP_MAX_ATTEMPTS")
    db_bootstrap_sleep_seconds: int = Field(default=2, alias="DB_BOOTSTRAP_SLEEP_SECONDS")


class AppSettings(BaseSettings):
    """Main application settings aggregating all configuration sections."""

    # App metadata
    app_name: str = "WeatherAI"
    env: str = Field(default="dev", alias="ENV")
    debug: bool = Field(default=True)
    version: str = "0.1.0"
    app_env: str = Field(default="development", alias="APP_ENV")

    # Configuration sections
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    openai: OpenAISettings = OpenAISettings()
    security: SecuritySettings = SecuritySettings()
    features: FeatureFlags = FeatureFlags()
    weather_data: WeatherDataSettings = WeatherDataSettings()
    rate_limit: RateLimitSettings = RateLimitSettings()
    cache: CacheSettings = CacheSettings()
    rag: RAGSettings = RAGSettings()
    observability: ObservabilitySettings = ObservabilitySettings()
    analytics: AnalyticsSettings = AnalyticsSettings()
    digest: DigestSettings = DigestSettings()
    db_bootstrap: DatabaseBootstrapSettings = DatabaseBootstrapSettings()

    # Backward compatibility properties for old config.py style access
    @property
    def cors_origins(self) -> list[str]:
        return self.security.cors_origins

    @property
    def database_url(self) -> str:
        return self.database.url
    
    @property
    def database_url_sync(self) -> str:
        """Build PostgreSQL connection string for SQLAlchemy sync (for migrations)."""
        import urllib.parse
        password_encoded = urllib.parse.quote_plus(self.database.password)
        return f"postgresql+psycopg://{self.database.user}:{password_encoded}@{self.database.host}:{self.database.port}/{self.database.name}"
    
    # Flattened access for backward compatibility with old config.py
    @property
    def postgres_host(self) -> str:
        return self.database.host
    
    @property
    def postgres_port(self) -> int:
        return self.database.port
    
    @property
    def postgres_db(self) -> str:
        return self.database.name
    
    @property
    def postgres_user(self) -> str:
        return self.database.user
    
    @property
    def postgres_password(self) -> str:
        return self.database.password
    
    @property
    def redis_url(self) -> str:
        return self.redis.url
    
    @property
    def jwt_secret(self) -> str:
        return self.security.jwt_secret
    
    @property
    def jwt_algorithm(self) -> str:
        return self.security.jwt_algorithm
    
    @property
    def jwt_access_token_expire_minutes(self) -> int:
        return self.security.jwt_access_token_expire_minutes
    
    @property
    def openai_api_key(self) -> str | None:
        return self.openai.api_key
    
    @property
    def openai_model(self) -> str:
        return self.openai.model
    
    @property
    def azure_openai_endpoint(self) -> str | None:
        return self.openai.azure_endpoint
    
    @property
    def azure_openai_api_key(self) -> str | None:
        return self.openai.azure_api_key
    
    @property
    def azure_openai_embedding_deployment(self) -> str | None:
        return self.openai.azure_embedding_deployment
    
    @property
    def azure_openai_embedding_dim(self) -> int:
        return self.openai.azure_embedding_dim
    
    @property
    def azure_openai_chat_deployment(self) -> str | None:
        return self.openai.azure_chat_deployment
    
    @property
    def disable_ingest_in_dev(self) -> bool:
        return self.features.disable_ingest_in_dev
    
    @property
    def openmeteo_base_url(self) -> str:
        return self.weather_data.openmeteo_base_url
    
    @property
    def enable_metar(self) -> bool:
        return self.features.enable_metar
    
    @property
    def metar_base_url(self) -> str:
        return self.weather_data.metar_base_url
    
    @property
    def ingest_interval_minutes(self) -> int:
        return self.weather_data.ingest_interval_minutes
    
    @property
    def max_locations_per_ingest(self) -> int:
        return self.weather_data.max_locations_per_ingest
    
    @property
    def openmeteo_air_quality_strict(self) -> bool:
        return self.weather_data.openmeteo_air_quality_strict
    
    @property
    def rate_limit_requests_per_minute(self) -> int:
        return self.rate_limit.requests_per_minute
    
    @property
    def llm_rate_limit_requests_per_minute(self) -> int:
        return self.rate_limit.llm_requests_per_minute
    
    @property
    def digest_cache_ttl_seconds(self) -> int:
        return self.cache.digest_cache_ttl_seconds
    
    @property
    def digest_use_llm(self) -> bool:
        return self.digest.use_llm
    
    @property
    def rag_chunk_size(self) -> int:
        return self.rag.chunk_size
    
    @property
    def rag_chunk_overlap(self) -> int:
        return self.rag.chunk_overlap
    
    @property
    def rag_similarity_threshold(self) -> float:
        return self.rag.similarity_threshold
    
    @property
    def rag_top_k(self) -> int:
        return self.rag.top_k
    
    @property
    def rag_mmr_lambda(self) -> float:
        return self.rag.mmr_lambda
    
    @property
    def rag_answer_cache_ttl_seconds(self) -> int:
        return self.rag.answer_cache_ttl_seconds
    
    @property
    def rag_embedding_cache_ttl_seconds(self) -> int:
        return self.rag.embedding_cache_ttl_seconds
    
    @property
    def rag_enable_mmr(self) -> bool:
        return self.rag.enable_mmr
    
    @property
    def rag_max_query_length(self) -> int:
        return self.rag.max_query_length
    
    @property
    def rag_stream_rate_limit(self) -> int:
        return self.rag.stream_rate_limit
    
    @property
    def rag_stream_rate_window_seconds(self) -> int:
        return self.rag.stream_rate_window_seconds
    
    @property
    def analytics_max_range_days(self) -> int:
        return self.analytics.max_range_days
    
    @property
    def use_redis_rate_limit(self) -> bool:
        return self.rate_limit.use_redis_rate_limit
    
    @property
    def redis_cache_analytics_ttl(self) -> int:
        return self.cache.redis_cache_analytics_ttl
    
    @property
    def redis_cache_forecast_ttl(self) -> int:
        return self.cache.redis_cache_forecast_ttl
    
    @property
    def no_refresh(self) -> bool:
        return self.analytics.no_refresh
    
    @property
    def environment(self) -> str:
        return self.observability.environment
    
    @property
    def otlp_endpoint(self) -> str | None:
        return self.observability.otlp_endpoint
    
    @property
    def enable_prometheus_metrics(self) -> bool:
        return self.features.enable_prometheus_metrics
    
    @property
    def metrics_auth_token(self) -> str | None:
        return self.observability.metrics_auth_token
    
    @property
    def json_logs(self) -> bool:
        return self.features.json_logs
    
    @property
    def enable_tracing(self) -> bool:
        return self.features.enable_tracing
    
    @property
    def trace_sample_rate(self) -> float:
        return self.observability.trace_sample_rate
    
    @property
    def enable_cost_tracking(self) -> bool:
        return self.features.enable_cost_tracking
    
    @property
    def cost_tracking_sampling_rate(self) -> float:
        return self.observability.cost_tracking_sampling_rate
    
    @property
    def skip_db_bootstrap(self) -> bool:
        return self.db_bootstrap.skip_db_bootstrap
    
    @property
    def db_bootstrap_max_attempts(self) -> int:
        return self.db_bootstrap.db_bootstrap_max_attempts
    
    @property
    def db_bootstrap_sleep_seconds(self) -> int:
        return self.db_bootstrap.db_bootstrap_sleep_seconds
    
    @property
    def log_level(self) -> str:
        return self.observability.log_level
    
    @property
    def sqlalchemy_echo(self) -> bool:
        return self.observability.sqlalchemy_echo
    
    @property
    def enable_metrics(self) -> bool:
        return self.features.enable_metrics

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields to be ignored



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


@lru_cache
def get_settings() -> AppSettings:
    """Get cached application settings."""
    settings = AppSettings()
    load_secrets_from_key_vault(settings)
    return settings


# Global settings instance for backward compatibility
settings = get_settings()
