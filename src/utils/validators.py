"""
Input Validation Utilities

This module provides validation functions for user inputs to ensure
security and data integrity.
"""

from urllib.parse import urlparse
from pathlib import Path
import re
from typing import Tuple

from src.core.constants import ALLOWED_IMAGE_EXTENSIONS, DEFAULT_MAX_IMAGE_SIZE_MB
from src.core.exceptions import InvalidInputError


def validate_image_url(url: str, max_size_mb: int = DEFAULT_MAX_IMAGE_SIZE_MB) -> Tuple[bool, str]:
    """Validate image URL for security and format.
    
    Args:
        url: Image URL to validate
        max_size_mb: Maximum allowed image size in MB
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
        If valid, error_message is empty string
    
    Raises:
        InvalidInputError: If URL is fundamentally invalid
    """
    if not url:
        return False, "URL cannot be empty"
    
    # Basic string validation
    if not isinstance(url, str):
        return False, "URL must be a string"
    
    if len(url) > 2048:  # RFC 7230 recommendation
        return False, "URL too long (max 2048 characters)"
    
    try:
        parsed = urlparse(url)
        
        # Check scheme
        if parsed.scheme not in ["http", "https"]:
            return False, "Only HTTP/HTTPS URLs are allowed"
        
        # Check if netloc (domain) exists
        if not parsed.netloc:
            return False, "Invalid URL format: missing domain"
        
        # Check for suspicious patterns (basic security)
        if any(char in url for char in ['<', '>', '"', "'"]):
            return False, "URL contains invalid characters"
        
        # Check file extension
        path_lower = parsed.path.lower()
        if not any(path_lower.endswith(ext) for ext in ALLOWED_IMAGE_EXTENSIONS):
            return False, f"Invalid image format. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        
        return True, ""
    
    except Exception as e:
        return False, f"Invalid URL: {str(e)}"


def validate_team_name(team_name: str) -> Tuple[bool, str]:
    """Validate CFL team name.
    
    Args:
        team_name: Team name to validate
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not team_name:
        return False, "Team name cannot be empty"
    
    if not isinstance(team_name, str):
        return False, "Team name must be a string"
    
    if len(team_name) > 100:
        return False, "Team name too long"
    
    # Allow letters, spaces, hyphens
    if not re.match(r'^[A-Za-z\s\-]+$', team_name):
        return False, "Team name contains invalid characters"
    
    return True, ""


def validate_jersey_number(number: str | int) -> Tuple[bool, str]:
    """Validate jersey number.
    
    Args:
        number: Jersey number to validate (string or int)
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if number is None:
        return False, "Jersey number cannot be None"
    
    try:
        num = int(number)
        
        # CFL jersey numbers are typically 0-99
        if num < 0 or num > 99:
            return False, "Jersey number must be between 0 and 99"
        
        return True, ""
    
    except (ValueError, TypeError):
        return False, "Jersey number must be a valid integer"


def validate_confidence_level(confidence: str) -> Tuple[bool, str]:
    """Validate confidence level value.
    
    Args:
        confidence: Confidence level to validate
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    from src.core.constants import VALID_CONFIDENCE_LEVELS
    
    if not confidence:
        return False, "Confidence level cannot be empty"
    
    if not isinstance(confidence, str):
        return False, "Confidence level must be a string"
    
    if confidence.lower() not in VALID_CONFIDENCE_LEVELS:
        return False, f"Invalid confidence level. Must be one of: {', '.join(VALID_CONFIDENCE_LEVELS)}"
    
    return True, ""


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem storage.
    
    Removes potentially dangerous characters and limits length.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename safe for storage
    """
    # Remove path separators and other dangerous characters
    filename = re.sub(r'[/\\:*?"<>|]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename or 'unnamed'


def validate_file_path(path: str, must_exist: bool = False) -> Tuple[bool, str]:
    """Validate file path for security.
    
    Args:
        path: File path to validate
        must_exist: If True, path must exist
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not path:
        return False, "Path cannot be empty"
    
    if not isinstance(path, str):
        return False, "Path must be a string"
    
    try:
        file_path = Path(path)
        
        # Check for path traversal attempts
        if '..' in path:
            return False, "Path traversal not allowed"
        
        # Check if path is absolute (safer than relative)
        # Note: This check can be relaxed based on requirements
        
        if must_exist and not file_path.exists():
            return False, f"Path does not exist: {path}"
        
        return True, ""
    
    except Exception as e:
        return False, f"Invalid path: {str(e)}"


def validate_json_structure(data: dict, required_fields: list[str]) -> Tuple[bool, str]:
    """Validate JSON data structure has required fields.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not isinstance(data, dict):
        return False, "Data must be a dictionary"
    
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, ""
