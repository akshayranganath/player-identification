"""
Centralized Logging Configuration

This module provides structured logging configuration for the application.
Supports both development (human-readable) and production (JSON) formats.
"""

import logging
import sys
from typing import Literal
from pathlib import Path


def configure_logging(
    log_level: str = "INFO",
    log_format: Literal["console", "json"] = "console",
    log_file: str | None = None
) -> None:
    """Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format - "console" for human-readable, "json" for structured
        log_file: Optional file path to write logs to
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatters
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = ConsoleFormatter()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set level for noisy third-party libraries
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    logging.info(f"Logging configured: level={log_level}, format={log_format}")


class ConsoleFormatter(logging.Formatter):
    """Human-readable console formatter with colors (if terminal supports it)."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def __init__(self, use_colors: bool = True):
        """Initialize formatter.
        
        Args:
            use_colors: Whether to use ANSI colors (auto-detected if not specified)
        """
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.use_colors = use_colors and sys.stdout.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with optional colors.
        
        Args:
            record: Log record to format
        
        Returns:
            Formatted log string
        """
        if self.use_colors:
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = (
                    f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
                )
        
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging (production use)."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: Log record to format
        
        Returns:
            JSON-formatted log string
        """
        import json
        from datetime import datetime
        
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.
    
    This is a convenience wrapper around logging.getLogger that provides
    type hints and documentation.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class RequestContextLogger(logging.LoggerAdapter):
    """Logger adapter that adds request context to log messages.
    
    Useful for tracking requests through the system.
    
    Example:
        >>> logger = RequestContextLogger(logging.getLogger(__name__), {"request_id": "abc123"})
        >>> logger.info("Processing request")
        # Output includes request_id
    """
    
    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        """Process log message to add context.
        
        Args:
            msg: Log message
            kwargs: Logging kwargs
        
        Returns:
            Tuple of (message, kwargs) with context added
        """
        # Add context to extra fields
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        
        # Add context to message if in console format
        context_str = ", ".join(f"{k}={v}" for k, v in self.extra.items())
        return f"[{context_str}] {msg}", kwargs


if __name__ == "__main__":
    # Test logging configuration
    print("Testing console format:")
    configure_logging(log_level="DEBUG", log_format="console")
    
    logger = get_logger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("\n" + "="*50 + "\n")
    print("Testing JSON format:")
    configure_logging(log_level="INFO", log_format="json")
    
    logger = get_logger(__name__)
    logger.info("This is a JSON formatted message")
    
    print("\n" + "="*50 + "\n")
    print("Testing request context logger:")
    configure_logging(log_level="INFO", log_format="console")
    context_logger = RequestContextLogger(
        logger,
        {"request_id": "req-12345", "user_id": "user-789"}
    )
    context_logger.info("Processing request with context")
