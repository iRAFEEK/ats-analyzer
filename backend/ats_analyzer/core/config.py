"""Application configuration."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./ats.db",
        env="DATABASE_URL"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # OpenAI
    OPENAI_API_KEY: str = Field(
        default="",
        env="OPENAI_API_KEY",
        description="OpenAI API key for AI-powered analysis"
    )
    
    # CORS
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="ALLOWED_ORIGINS"
    )
    
    # Production settings
    ENVIRONMENT: str = Field(
        default="development",
        env="ENVIRONMENT",
        description="Environment (development/production)"
    )
    
    # File storage
    UPLOAD_DIR: str = Field(
        default="/tmp/ats_uploads",
        env="UPLOAD_DIR"
    )
    MAX_FILE_SIZE: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        env="MAX_FILE_SIZE"
    )
    
    # OCR
    TESSERACT_CMD: str = Field(
        default="tesseract",
        env="TESSERACT_CMD"
    )
    
    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        env="LOG_LEVEL"
    )
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


@lru_cache()
def get_scoring_config() -> dict[str, Any]:
    """Load scoring configuration from YAML."""
    config_path = Path(__file__).parent.parent.parent / "config" / "scoring.yaml"
    
    if not config_path.exists():
        # Return default config if file doesn't exist
        return {
            "similarity_thresholds": {
                "required_hit": 0.75,
                "preferred_hit": 0.75,
                "weak_support": 0.65,
            },
            "weights": {
                "coverage": 0.6,
                "experience": 0.3,
                "education": 0.1,
            },
            "section_weights": {
                "experience": 1.0,
                "projects": 0.8,
                "skills": 0.4,
            },
            "recency_years_boost": 2,
        }
    
    with open(config_path, "r") as f:
        return yaml.safe_load(f)
