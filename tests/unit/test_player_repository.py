"""
Unit tests for player repository.
"""

import pytest
from src.repositories.player_repository import PlayerRepository


def test_find_existing_player(temp_player_db):
    """Test finding an existing player."""
    repo = PlayerRepository(temp_player_db)
    
    player_name = repo.find_by_team_and_number("Montreal Alouettes", "10")
    assert player_name == "Davis Alexander"


def test_find_nonexistent_player(temp_player_db):
    """Test finding a non-existent player."""
    repo = PlayerRepository(temp_player_db)
    
    player_name = repo.find_by_team_and_number("Montreal Alouettes", "99")
    assert player_name is None


def test_find_nonexistent_team(temp_player_db):
    """Test finding player from non-existent team."""
    repo = PlayerRepository(temp_player_db)
    
    player_name = repo.find_by_team_and_number("Invalid Team", "10")
    assert player_name is None


def test_get_all_teams(temp_player_db):
    """Test getting all team names."""
    repo = PlayerRepository(temp_player_db)
    
    teams = repo.get_all_teams()
    assert "Montreal Alouettes" in teams
    assert "Saskatchewan Roughriders" in teams
    assert "BC Lions" in teams
    assert len(teams) == 3


def test_team_exists(temp_player_db):
    """Test checking if team exists."""
    repo = PlayerRepository(temp_player_db)
    
    assert repo.team_exists("Montreal Alouettes") == True
    assert repo.team_exists("Invalid Team") == False


def test_get_team_roster(temp_player_db):
    """Test getting team roster."""
    repo = PlayerRepository(temp_player_db)
    
    roster = repo.get_team_roster("Montreal Alouettes")
    assert "10" in roster
    assert "7" in roster
    assert roster["10"] == "Davis Alexander"
