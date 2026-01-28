"""
Unit tests for input validators.
"""

import pytest
from src.utils.validators import (
    validate_image_url,
    validate_team_name,
    validate_jersey_number,
    validate_confidence_level,
    sanitize_filename
)


class TestImageURLValidation:
    """Tests for image URL validation."""
    
    def test_valid_http_url(self):
        """Test valid HTTP URLs."""
        is_valid, msg = validate_image_url("http://example.com/image.jpg")
        assert is_valid == True
        assert msg == ""
    
    def test_valid_https_url(self):
        """Test valid HTTPS URLs."""
        is_valid, msg = validate_image_url("https://example.com/image.png")
        assert is_valid == True
    
    def test_invalid_scheme(self):
        """Test invalid URL schemes."""
        is_valid, msg = validate_image_url("ftp://example.com/image.jpg")
        assert is_valid == False
        assert "HTTP/HTTPS" in msg
    
    def test_invalid_extension(self):
        """Test invalid file extensions."""
        is_valid, msg = validate_image_url("https://example.com/file.txt")
        assert is_valid == False
        assert "Invalid image format" in msg
    
    def test_empty_url(self):
        """Test empty URL."""
        is_valid, msg = validate_image_url("")
        assert is_valid == False
        assert "empty" in msg.lower()


class TestTeamNameValidation:
    """Tests for team name validation."""
    
    def test_valid_team_name(self):
        """Test valid team names."""
        is_valid, msg = validate_team_name("Montreal Alouettes")
        assert is_valid == True
    
    def test_empty_team_name(self):
        """Test empty team name."""
        is_valid, msg = validate_team_name("")
        assert is_valid == False
    
    def test_invalid_characters(self):
        """Test team name with invalid characters."""
        is_valid, msg = validate_team_name("Team@123")
        assert is_valid == False


class TestJerseyNumberValidation:
    """Tests for jersey number validation."""
    
    def test_valid_number_string(self):
        """Test valid jersey number as string."""
        is_valid, msg = validate_jersey_number("10")
        assert is_valid == True
    
    def test_valid_number_int(self):
        """Test valid jersey number as int."""
        is_valid, msg = validate_jersey_number(10)
        assert is_valid == True
    
    def test_out_of_range(self):
        """Test out of range numbers."""
        is_valid, msg = validate_jersey_number(100)
        assert is_valid == False
        
        is_valid, msg = validate_jersey_number(-1)
        assert is_valid == False
    
    def test_invalid_format(self):
        """Test invalid number format."""
        is_valid, msg = validate_jersey_number("abc")
        assert is_valid == False


class TestFileSanitization:
    """Tests for filename sanitization."""
    
    def test_remove_dangerous_chars(self):
        """Test removal of dangerous characters."""
        result = sanitize_filename("test/file\\name:test")
        assert "/" not in result
        assert "\\" not in result
        assert ":" not in result
    
    def test_length_limit(self):
        """Test filename length limiting."""
        long_name = "a" * 300 + ".jpg"
        result = sanitize_filename(long_name)
        assert len(result) <= 255
    
    def test_empty_filename(self):
        """Test empty filename."""
        result = sanitize_filename("")
        assert result == "unnamed"
