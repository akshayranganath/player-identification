"""
Pytest Configuration and Fixtures

This module provides common fixtures and configuration for all tests.
"""

import pytest
from pathlib import Path
import json


@pytest.fixture
def sample_player_data():
    """Sample player database data for testing."""
    return {
        "Montreal Alouettes": {
            "10": "Davis Alexander",
            "7": "Cody Fajardo"
        },
        "Saskatchewan Roughriders": {
            "7": "Trevor Harris",
            "88": "Samuel Emilus"
        },
        "BC Lions": {
            "12": "Nathan Rourke"
        }
    }


@pytest.fixture
def sample_vision_response():
    """Sample vision agent response."""
    return {
        "image_analysis": {
            "total_players_visible": 1,
            "image_quality": "good",
            "viewing_angle": "front"
        },
        "players": [
            {
                "player_id": 1,
                "jersey_number": {
                    "value": "10",
                    "confidence": "high"
                },
                "team": {
                    "name": "Alouettes",
                    "colors_visible": ["red", "blue"],
                    "confidence": "high"
                },
                "visual_evidence": ["Jersey number 10 clearly visible"],
                "bounding_box": {"description": "center foreground"},
                "overall_confidence": "high"
            }
        ]
    }


@pytest.fixture
def sample_search_response():
    """Sample search agent response."""
    return {
        "player_name": "Davis Alexander",
        "confidence": "high",
        "reasoning": "Multiple sources confirm this player",
        "sources": ["https://www.cfl.ca/players/"]
    }


@pytest.fixture
def temp_player_db(tmp_path, sample_player_data):
    """Create temporary player database file."""
    db_file = tmp_path / "test_players.json"
    with open(db_file, 'w') as f:
        json.dump(sample_player_data, f)
    return str(db_file)


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock application settings."""
    from src.core.config import Settings
    
    settings = Settings(
        serp_api_key="test_key_1234567890",
        aws_region="us-east-1",
        bedrock_model_id="test-model",
        max_image_size_mb=10,
        request_timeout=30,
        max_retries=3
    )
    
    def mock_get_settings():
        return settings
    
    monkeypatch.setattr("src.core.config.get_settings", mock_get_settings)
    return settings
