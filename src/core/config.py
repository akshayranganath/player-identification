"""
Centralized Configuration Management

This module provides type-safe configuration management using Pydantic Settings.
Secrets are loaded from .env files with validation and permission checks.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache
import os
from pathlib import Path
import stat
import warnings
from typing import Literal


class Settings(BaseSettings):
    """Application settings with validation.
    
    All settings can be overridden via environment variables.
    Settings are loaded from .env file if present.
    """
    
    # ==============================================================================
    # API KEYS (REQUIRED)
    # ==============================================================================
    
    serp_api_key: str = Field(
        ..., 
        min_length=10,
        description="SerpAPI key for web search functionality"
    )
    
    # ==============================================================================
    # AWS CONFIGURATION
    # ==============================================================================
    
    aws_region: str = Field(
        default="us-east-1",
        description="AWS region for Bedrock API calls"
    )
    
    aws_profile: str | None = Field(
        default=None,
        description="AWS profile name from ~/.aws/credentials"
    )
    
    bedrock_model_id: str = Field(
        default="anthropic.claude-3-sonnet-20240229-v1:0",
        description="AWS Bedrock model ID for Claude"
    )
    
    # ==============================================================================
    # APPLICATION SETTINGS
    # ==============================================================================
    
    max_image_size_mb: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum allowed image size in megabytes"
    )
    
    request_timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Request timeout in seconds"
    )
    
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for failed requests"
    )
    
    rate_limit_per_minute: int = Field(
        default=60,
        ge=1,
        le=1000,
        description="Rate limit for API calls per minute"
    )
    
    # ==============================================================================
    # LOGGING
    # ==============================================================================
    
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    
    # ==============================================================================
    # ENVIRONMENT
    # ==============================================================================
    
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment"
    )
    
    # ==============================================================================
    # DATABASE
    # ==============================================================================
    
    player_db_path: str = Field(
        default="data/db/cfl_players.json",
        description="Path to player database JSON file"
    )
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env
    
    @field_validator("serp_api_key")
    @classmethod
    def validate_serp_key(cls, v: str) -> str:
        """Validate SERP API key format."""
        if not v or v == "your_serpapi_key_here":
            raise ValueError(
                "SERP_API_KEY not configured. "
                "Copy .env.example to .env and add your key."
            )
        if len(v) < 10:
            raise ValueError("SERP_API_KEY appears to be invalid (too short)")
        return v
    
    def validate_env_file_permissions(self) -> None:
        """Warn if .env file has insecure permissions.
        
        Checks that .env file (if exists) has restrictive permissions
        (600 = owner read/write only) on Unix-like systems.
        """
        env_path = Path(".env")
        if not env_path.exists():
            return
        
        # Check file permissions (Unix-like systems only)
        if os.name != 'nt':  # Not Windows
            try:
                file_stat = env_path.stat()
                file_mode = stat.S_IMODE(file_stat.st_mode)
                
                # Check if file is readable by group or others
                if file_mode & (stat.S_IRGRP | stat.S_IROTH):
                    warnings.warn(
                        f".env file has insecure permissions: {oct(file_mode)}. "
                        f"Secrets may be readable by other users. "
                        f"Run: chmod 600 .env",
                        UserWarning,
                        stacklevel=2
                    )
            except OSError as e:
                warnings.warn(
                    f"Could not check .env file permissions: {e}",
                    UserWarning,
                    stacklevel=2
                )
    
    def mask_secrets(self) -> dict:
        """Return configuration with masked secrets for safe logging.
        
        Returns:
            Dictionary with sensitive values masked (showing first/last 4 chars)
        """
        config_dict = self.model_dump()
        secret_fields = ["serp_api_key"]
        
        for field in secret_fields:
            if field in config_dict and config_dict[field]:
                value = str(config_dict[field])
                # Show first 4 and last 4 characters
                if len(value) > 8:
                    config_dict[field] = f"{value[:4]}...{value[-4:]}"
                else:
                    config_dict[field] = "***"
        
        return config_dict


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    This function is cached to ensure we only load settings once.
    Settings are loaded from .env file and environment variables.
    
    Returns:
        Settings instance with validated configuration
    
    Raises:
        ValueError: If required settings are missing or invalid
    """
    settings = Settings()
    settings.validate_env_file_permissions()
    return settings


def validate_configuration() -> None:
    """Validate configuration at application startup.
    
    This function should be called at application startup to ensure
    all required configuration is present and valid.
    
    Raises:
        ValueError: If configuration is invalid
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        settings = get_settings()
        
        # Log masked config (safe for logs)
        logger.info("Configuration loaded successfully")
        logger.debug(f"Configuration: {settings.mask_secrets()}")
        
        # Check .env file exists
        env_path = Path(".env")
        if not env_path.exists():
            logger.warning(
                ".env file not found. Using environment variables only. "
                "Consider creating .env from .env.example for local development."
            )
        
        # Verify database file exists
        db_path = Path(settings.player_db_path)
        if not db_path.exists():
            logger.warning(
                f"Player database not found at: {settings.player_db_path}. "
                f"Some functionality may not work correctly."
            )
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise


if __name__ == "__main__":
    # Test configuration loading
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        settings = get_settings()
        print("✓ Configuration loaded successfully")
        print("\nConfiguration (secrets masked):")
        import json
        print(json.dumps(settings.mask_secrets(), indent=2))
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        exit(1)
