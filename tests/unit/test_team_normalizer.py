"""
Unit tests for team name normalization.
"""

import pytest
from src.utils.team_normalizer import TeamNormalizer, normalize_team_name


def test_normalize_short_name():
    """Test normalizing short team names."""
    normalizer = TeamNormalizer()
    
    assert normalizer.normalize("Alouettes") == "Montreal Alouettes"
    assert normalizer.normalize("Roughriders") == "Saskatchewan Roughriders"
    assert normalizer.normalize("Lions") == "BC Lions"


def test_normalize_full_name():
    """Test that full names are unchanged."""
    normalizer = TeamNormalizer()
    
    assert normalizer.normalize("Montreal Alouettes") == "Montreal Alouettes"
    assert normalizer.normalize("BC Lions") == "BC Lions"


def test_normalize_case_insensitive():
    """Test case-insensitive normalization."""
    normalizer = TeamNormalizer()
    
    assert normalizer.normalize("alouettes") == "Montreal Alouettes"
    assert normalizer.normalize("LIONS") == "BC Lions"


def test_normalize_unknown():
    """Test normalizing unknown team names."""
    normalizer = TeamNormalizer()
    
    assert normalizer.normalize("Unknown") == "Unknown"
    assert normalizer.normalize("InvalidTeam") == "InvalidTeam"


def test_is_valid_team():
    """Test team validation."""
    normalizer = TeamNormalizer()
    
    assert normalizer.is_valid_team("Alouettes") == True
    assert normalizer.is_valid_team("Montreal Alouettes") == True
    assert normalizer.is_valid_team("InvalidTeam") == False
    assert normalizer.is_valid_team("Unknown") == False


def test_module_level_function():
    """Test module-level convenience function."""
    assert normalize_team_name("Alouettes") == "Montreal Alouettes"
    assert normalize_team_name("Lions") == "BC Lions"
