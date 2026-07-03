import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Resolve the root directory of the workspace
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
env_path = BASE_DIR / ".env"

# Load environment variables from .env
load_dotenv(dotenv_path=env_path)

class Settings(BaseModel):
    """
    Application settings model that loads and validates environment variables.
    """
    APP_NAME: str = Field(default_factory=lambda: os.getenv("APP_NAME", "ProposalPilot AI"))
    APP_VERSION: str = Field(default_factory=lambda: os.getenv("APP_VERSION", "1.0.0"))
    APP_ENV: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    DEBUG: bool = Field(default_factory=lambda: os.getenv("DEBUG", "True").lower() in ("true", "1", "yes"))
    
    HOST: str = Field(default_factory=lambda: os.getenv("HOST", "127.0.0.1"))
    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    
    GROQ_API_KEY: str = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    GROQ_MODEL: str = Field(default_factory=lambda: os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))
    
    LOG_LEVEL: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    LOG_FILE: str = Field(default_factory=lambda: os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "proposal_pilot.log")))
    LOG_ROTATION: str = Field(default_factory=lambda: os.getenv("LOG_ROTATION", "10 MB"))
    LOG_RETENTION: str = Field(default_factory=lambda: os.getenv("LOG_RETENTION", "10 days"))
    
    OUTPUT_DIR: str = Field(default_factory=lambda: os.getenv("OUTPUT_DIR", "generated_docs"))
    
    MAX_RETRIES: int = Field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    REQUEST_TIMEOUT: float = Field(default_factory=lambda: float(os.getenv("REQUEST_TIMEOUT", "60.0")))

# Global settings instance
settings = Settings()
