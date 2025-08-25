"""Centralized settings management for WeatherAI.

This module provides typed configuration sections and centralized
settings loading for all application components.
"""

from __future__ import annotations
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    server: str = Field(default="localhost", alias="DB_SERVER")
    port: int = Field(default=1433, alias="DB_PORT")
    name: str = Field(default="WeatherAI", alias="DB_NAME")
    user: str = Field(default="sa", alias="DB_USER")
    password: str = Field(default="YourStrong@Passw0rd", alias="DB_PASSWORD")
    
    @property
    def url(self) -> str:
        """Get SQLAlchemy database URL."""
        import urllib.parse
        password_encoded = urllib.parse.quote_plus(self.password)
        return f"mssql+aioodbc://{self.user}:{password_encoded}@{self.server}:{self.port}/{self.name}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    
    url: str = Field(default="redis://redis:6379", alias="REDIS_URL")
    max_connections: int = Field(default=20, alias="REDIS_MAX_CONNECTIONS")
    socket_timeout: int = Field(default=5, alias="REDIS_SOCKET_TIMEOUT")


class OpenAISettings(BaseSettings):
    """OpenAI API configuration settings."""
    
    api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    model: str = Field(default="gpt-4", alias="OPENAI_MODEL")
    max_tokens: int = Field(default=2000, alias="OPENAI_MAX_TOKENS")
    temperature: float = Field(default=0.1, alias="OPENAI_TEMPERATURE")
    timeout: int = Field(default=30, alias="OPENAI_TIMEOUT_SECONDS")


class SecuritySettings(BaseSettings):
    """Security and authentication settings."""
    
    jwt_secret: str = Field(default="change-this-secret-key", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"], 
        alias="CORS_ORIGINS"
    )
    
    @field_validator("cors_origins", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


class FeatureFlags(BaseSettings):
    """Feature flags for enabling/disabling functionality."""
    
    enable_rag: bool = Field(default=True, alias="FEATURE_ENABLE_RAG")
    enable_analytics: bool = Field(default=True, alias="FEATURE_ENABLE_ANALYTICS")
    enable_caching: bool = Field(default=True, alias="FEATURE_ENABLE_CACHING")
    enable_rate_limiting: bool = Field(default=True, alias="FEATURE_ENABLE_RATE_LIMITING")


class AppSettings(BaseSettings):
    """Main application settings aggregating all configuration sections."""
    
    # App metadata
    app_name: str = "WeatherAI"
    env: str = Field(default="dev", alias="ENV")
    debug: bool = Field(default=True)
    version: str = "0.1.0"
    
    # Configuration sections
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    openai: OpenAISettings = OpenAISettings()
    security: SecuritySettings = SecuritySettings()
    features: FeatureFlags = FeatureFlags()
    
    # Backward compatibility properties
    @property
    def cors_origins(self) -> List[str]:
        return self.security.cors_origins
    
    @property
    def database_url(self) -> str:
        return self.database.url


@lru_cache()
def get_settings() -> AppSettings:
    """Get cached application settings."""
    return AppSettings()


# Global settings instance for backward compatibility
settings = get_settings()