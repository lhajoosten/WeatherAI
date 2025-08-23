import urllib.parse

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "WeatherAI"
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True)

    # Database - MSSQL
    db_server: str = Field(default="sqlserver", alias="DB_SERVER")
    db_port: int = Field(default=1433, alias="DB_PORT")
    db_name: str = Field(default="WeatherAI", alias="DB_NAME")
    db_user: str = Field(default="sa", alias="DB_USER")
    db_password: str = Field(default="Your_password123", alias="DB_PASSWORD")

    # Redis
    redis_url: str = Field(default="redis://redis:6379", alias="REDIS_URL")

    # JWT
    jwt_secret: str = Field(default="change-this-secret-key", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    # OpenAI
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", alias="OPENAI_MODEL")

    # Weather Data Ingestion
    openmeteo_base_url: str = Field(default="https://api.open-meteo.com", alias="OPENMETEO_BASE_URL")
    enable_metar: bool = Field(default=False, alias="ENABLE_METAR")
    metar_base_url: str = Field(default="https://aviationweather.gov/adds/dataserver_current/httpparam", alias="METAR_BASE_URL")
    ingest_interval_minutes: int = Field(default=120, alias="INGEST_INTERVAL_MINUTES")
    max_locations_per_ingest: int = Field(default=25, alias="MAX_LOCATIONS_PER_INGEST")

    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=60, alias="RATE_LIMIT_REQUESTS_PER_MINUTE")
    llm_rate_limit_requests_per_minute: int = Field(default=10, alias="LLM_RATE_LIMIT_REQUESTS_PER_MINUTE")

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:5173", "http://localhost:3000"], alias="CORS_ORIGINS")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from environment variable (comma-separated or list)."""
        if isinstance(v, str):
            # Parse comma-separated string
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            # Add fallback origins if not present
            fallback_origins = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
            for fallback in fallback_origins:
                if fallback not in origins:
                    origins.append(fallback)
            return origins
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    def __init__(self, **data):
        super().__init__(**data)
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

# Global settings instance
settings = Settings()
