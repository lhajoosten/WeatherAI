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

    # Database - MSSQL
    db_server: str = Field(default="localhost", alias="DB_SERVER")
    db_port: int = Field(default=1433, alias="DB_PORT")
    db_name: str = Field(default="WeatherAI", alias="DB_NAME")
    db_user: str = Field(default="sa", alias="DB_USER")
    db_password: str = Field(default="YourStrong@Passw0rd", alias="DB_PASSWORD")

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

    # RAG Defaults
    rag_chunk_size: int = Field(default=512, alias="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(default=50, alias="RAG_CHUNK_OVERLAP")
    rag_similarity_threshold: float = Field(default=0.75, alias="RAG_SIMILARITY_THRESHOLD")
    rag_top_k: int = Field(default=6, alias="RAG_TOP_K")
    rag_mmr_lambda: float = Field(default=0.5, alias="RAG_MMR_LAMBDA")
    rag_answer_cache_ttl_seconds: int = Field(default=21600, alias="RAG_ANSWER_CACHE_TTL_SECONDS")

    # Analytics
    analytics_max_range_days: int = Field(default=30, alias="ANALYTICS_MAX_RANGE_DAYS")

    # Redis Cache Configuration
    use_redis_rate_limit: bool = Field(default=True, alias="USE_REDIS_RATE_LIMIT")
    redis_cache_analytics_ttl: int = Field(default=60, alias="REDIS_CACHE_ANALYTICS_TTL")
    redis_cache_forecast_ttl: int = Field(default=300, alias="REDIS_CACHE_FORECAST_TTL")

    # Analytics Pipeline
    no_refresh: bool = Field(default=False, alias="NO_REFRESH")

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
        """Build MSSQL connection string for SQLAlchemy with aioodbc (async)."""
        # Build raw ODBC connection string
        odbc_params = {
            "DRIVER": "{ODBC Driver 18 for SQL Server}",
            "SERVER": f"{self.db_server},{self.db_port}",
            "DATABASE": self.db_name,
            "UID": self.db_user,
            "PWD": self.db_password,
            "TrustServerCertificate": "yes",
        }

        # URL encode the connection string
        odbc_connect = ";".join([f"{k}={v}" for k, v in odbc_params.items()])
        encoded_connect = urllib.parse.quote_plus(odbc_connect)

        # Use aioodbc async dialect for SQLAlchemy
        return f"mssql+aioodbc:///?odbc_connect={encoded_connect}"

    @property
    def database_url_sync(self) -> str:
        """Build MSSQL connection string for SQLAlchemy with pyodbc (sync) for migrations."""
        # Build raw ODBC connection string
        odbc_params = {
            "DRIVER": "{ODBC Driver 18 for SQL Server}",
            "SERVER": f"{self.db_server},{self.db_port}",
            "DATABASE": self.db_name,
            "UID": self.db_user,
            "PWD": self.db_password,
            "TrustServerCertificate": "yes",
        }

        # URL encode the connection string
        odbc_connect = ";".join([f"{k}={v}" for k, v in odbc_params.items()])
        encoded_connect = urllib.parse.quote_plus(odbc_connect)

        # Use pyodbc sync dialect for Alembic migrations
        return f"mssql+pyodbc:///?odbc_connect={encoded_connect}"

    @property
    def master_database_url_sync(self) -> str:
        """Build MSSQL connection string for connecting to master database (for CREATE DATABASE)."""
        # Build raw ODBC connection string for master database
        odbc_params = {
            "DRIVER": "{ODBC Driver 18 for SQL Server}",
            "SERVER": f"{self.db_server},{self.db_port}",
            "DATABASE": "master",
            "UID": self.db_user,
            "PWD": self.db_password,
            "TrustServerCertificate": "yes",
        }

        # URL encode the connection string
        odbc_connect = ";".join([f"{k}={v}" for k, v in odbc_params.items()])
        encoded_connect = urllib.parse.quote_plus(odbc_connect)

        # Use pyodbc sync dialect for master database connection
        return f"mssql+pyodbc:///?odbc_connect={encoded_connect}"

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
