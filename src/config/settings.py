"""
Configuration settings for Premier League MCP Server
Manages environment variables and application settings
"""

import os
from typing import Optional, List, Dict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    # API Football Configuration
    RAPID_API_KEY_FOOTBALL: str = os.getenv("RAPID_API_KEY_FOOTBALL", "")
    
    # Premier League Specific
    PREMIER_LEAGUE_ID: int = 39
    DEFAULT_SEASON: int = 2025
    
    # Rate Limiting Configuration
    MAX_DAILY_REQUESTS: int = 1000
    RATE_LIMIT_WINDOW_HOURS: int = 24
    DEFAULT_REQUEST_MODE: str = "low"
    
    # Scraping Configuration
    ENABLE_LIVE_SCRAPING: bool = True
    SCRAPING_TIMEZONE: str = "UTC"
    BASE_API_URL: str = "https://v3.football.api-sports.io"
    
    # Cache Configuration
    DEFAULT_CACHE_TTL_HOURS: int = 24
    LIVE_DATA_TTL_MINUTES: int = 5
    
    # Server Configuration
    MCP_SERVER_HOST: str = "127.0.0.1"
    MCP_SERVER_PORT: int = 5000
    FASTAPI_HOST: str = "127.0.0.1"
    FASTAPI_PORT: int = 8000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    ENABLE_REQUEST_LOGGING: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def validate_required_settings(self) -> List[str]:
        """Validate that all required settings are present"""
        missing = []
        
        if not self.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not self.SUPABASE_ANON_KEY:
            missing.append("SUPABASE_ANON_KEY")
        if not self.RAPID_API_KEY_FOOTBALL:
            missing.append("RAPID_API_KEY_FOOTBALL")
            
        return missing
    
    def get_api_headers(self) -> Dict[str, str]:
        """Get headers for API Football requests"""
        return {
            "x-apisports-key": self.RAPID_API_KEY_FOOTBALL
        }
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the application settings"""
    return settings


def validate_environment() -> tuple:
    """Validate the environment configuration"""
    missing = settings.validate_required_settings()
    is_valid = len(missing) == 0
    return is_valid, missing
