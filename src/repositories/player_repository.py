"""
Player Repository

This module provides data access for CFL player information.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, List
from threading import Lock

from src.core.exceptions import DatabaseError
from src.core.config import get_settings

logger = logging.getLogger(__name__)


class PlayerRepository:
    """Repository for accessing CFL player data."""
    
    def __init__(self, db_path: str | None = None):
        """Initialize player repository.
        
        Args:
            db_path: Path to player database JSON file (uses config default if None)
        """
        if db_path is None:
            settings = get_settings()
            db_path = settings.player_db_path
        
        self.db_path = Path(db_path)
        self._data: Dict[str, Dict[str, str | List[str]]] = {}
        self._lock = Lock()  # Thread-safe access
        self._load_data()
    
    def _load_data(self) -> None:
        """Load player data from JSON file."""
        try:
            if not self.db_path.exists():
                logger.warning(f"Player database not found at: {self.db_path}")
                self._data = {}
                return
            
            with open(self.db_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
            
            logger.info(f"Loaded player data for {len(self._data)} teams")
        
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding player database JSON: {e}")
            raise DatabaseError(f"Invalid JSON in player database: {e}")
        
        except Exception as e:
            logger.error(f"Error loading player database: {e}")
            raise DatabaseError(f"Failed to load player database: {e}")
    
    def find_by_team_and_number(
        self,
        team: str,
        number: str
    ) -> Optional[str]:
        """Find player name by team and jersey number.
        
        Args:
            team: Team name (full official name)
            number: Jersey number as string
        
        Returns:
            Player name if found, None otherwise
        """
        with self._lock:
            if team not in self._data:
                logger.debug(f"Team '{team}' not found in database")
                return None
            
            team_data = self._data[team]
            number_str = str(number)
            
            if number_str not in team_data:
                logger.debug(f"Jersey number '{number}' not found for team '{team}'")
                return None
            
            player_name = team_data[number_str]
            
            # Handle case where multiple players have same number (list)
            if isinstance(player_name, list):
                player_name = player_name[0]  # Take first match
                logger.debug(f"Multiple players with number {number}, using: {player_name}")
            
            return player_name
    
    def get_all_teams(self) -> List[str]:
        """Get list of all team names in database.
        
        Returns:
            List of team names
        """
        with self._lock:
            return list(self._data.keys())
    
    def get_team_roster(self, team: str) -> Dict[str, str]:
        """Get all players for a team.
        
        Args:
            team: Team name
        
        Returns:
            Dictionary of {jersey_number: player_name}
        """
        with self._lock:
            return self._data.get(team, {})
    
    def team_exists(self, team: str) -> bool:
        """Check if team exists in database.
        
        Args:
            team: Team name
        
        Returns:
            True if team exists
        """
        with self._lock:
            return team in self._data
    
    def reload(self) -> None:
        """Reload player data from disk."""
        self._load_data()
