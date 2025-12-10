"""Application configuration settings."""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Flood Prediction API"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "flood_prediction"
    db_user: str = "flood_user"
    db_password: str = "flood_password"
    db_ssl: bool = False
    
    # Server
    port: int = 18080

    # Prediction source: "api" (live external) or "db" (use ld1_history table)
    prediction_source: str = "api"
    ld1_table: str = "ld1_history"
    
    @property
    def database_url(self) -> str:
        """Construct async database URL."""
        ssl_param = "?ssl=require" if self.db_ssl else ""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}{ssl_param}"
    
    @property
    def sync_database_url(self) -> str:
        """Construct sync database URL for migrations."""
        ssl_param = "?sslmode=require" if self.db_ssl else ""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}{ssl_param}"
    
    class Config:
        env_prefix = ""
        case_sensitive = False
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
