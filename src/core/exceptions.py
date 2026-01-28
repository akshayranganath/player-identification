"""
Custom Exception Hierarchy

This module defines custom exceptions for the player identification system.
All application-specific exceptions inherit from PlayerIdentificationError.
"""


class PlayerIdentificationError(Exception):
    """Base exception for player identification system.
    
    All custom exceptions should inherit from this class.
    """
    
    def __init__(self, message: str, details: dict | None = None):
        """Initialize exception with message and optional details.
        
        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """Return string representation of exception."""
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(PlayerIdentificationError):
    """Configuration is invalid or missing."""
    pass


class VisionAnalysisError(PlayerIdentificationError):
    """Vision agent failed to analyze image."""
    pass


class WebSearchError(PlayerIdentificationError):
    """Web search agent failed to find player information."""
    pass


class ImageDownloadError(PlayerIdentificationError):
    """Failed to download or process image."""
    pass


class InvalidInputError(PlayerIdentificationError):
    """Invalid input provided by user."""
    pass


class RateLimitError(PlayerIdentificationError):
    """Rate limit exceeded for external API."""
    pass


class DatabaseError(PlayerIdentificationError):
    """Database operation failed."""
    pass


class ValidationError(PlayerIdentificationError):
    """Data validation failed."""
    pass


class TimeoutError(PlayerIdentificationError):
    """Operation timed out."""
    pass


class AgentError(PlayerIdentificationError):
    """General agent execution error."""
    pass


class JSONParsingError(PlayerIdentificationError):
    """Failed to parse JSON response from agent."""
    pass
