from typing import Optional
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
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", alias="OPENAI_MODEL")
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=60, alias="RATE_LIMIT_REQUESTS_PER_MINUTE")
    llm_rate_limit_requests_per_minute: int = Field(default=10, alias="LLM_RATE_LIMIT_REQUESTS_PER_MINUTE")
    
    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:5173", "http://localhost:3000"], alias="CORS_ORIGINS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def database_url(self) -> str:
        """Build MSSQL connection string for SQLAlchemy with pyodbc."""
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
        
        return f"mssql+pyodbc:///?odbc_connect={encoded_connect}"


# Global settings instance
settings = Settings()