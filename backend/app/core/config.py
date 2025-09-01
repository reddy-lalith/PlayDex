from typing import List, Union, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "PlayDex"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS - Simple string that we'll parse manually
    BACKEND_CORS_ORIGINS: Optional[str] = "http://localhost:3000,http://localhost:3001"

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/playdex"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Debug
    DEBUG: bool = True
    
    # NBA API Settings
    NBA_API_KEY: str = ""
    
    # Gemini API Settings
    GEMINI_API_KEY: str = ""
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if self.BACKEND_CORS_ORIGINS:
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        return []
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()