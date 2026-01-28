"""
Team Name Normalization

This module provides utilities for normalizing CFL team names to ensure
consistent matching against the database.
"""

import logging
from typing import Optional

from src.core.constants import TEAM_NAME_MAPPING

logger = logging.getLogger(__name__)


class TeamNormalizer:
    """Normalizes CFL team names to standard database format."""
    
    def __init__(self):
        """Initialize team normalizer with mapping."""
        self.mapping = TEAM_NAME_MAPPING
    
    def normalize(self, team_name: str) -> str:
        """Normalize team name to standard database format.
        
        Args:
            team_name: Team name from vision model (may be short form or informal)
        
        Returns:
            Full official team name as it appears in database
            Returns original name if no mapping found
        
        Examples:
            >>> normalizer = TeamNormalizer()
            >>> normalizer.normalize("Alouettes")
            'Montreal Alouettes'
            >>> normalizer.normalize("Saskatchewan")
            'Saskatchewan Roughriders'
            >>> normalizer.normalize("Unknown")
            'Unknown'
        """
        if not team_name or team_name == "Unknown":
            return team_name
        
        # Try exact match first (case-sensitive)
        if team_name in self.mapping:
            normalized = self.mapping[team_name]
            if normalized != team_name:
                logger.debug(f"Normalized team name: '{team_name}' -> '{normalized}'")
            return normalized
        
        # Try case-insensitive match
        for key, value in self.mapping.items():
            if key.lower() == team_name.lower():
                logger.debug(
                    f"Normalized team name (case-insensitive): '{team_name}' -> '{value}'"
                )
                return value
        
        # No match found - return original and log warning
        logger.warning(
            f"Unknown team name: '{team_name}' - not found in mapping. "
            f"Database lookup may fail."
        )
        return team_name
    
    def is_valid_team(self, team_name: str) -> bool:
        """Check if team name is a known CFL team.
        
        Args:
            team_name: Team name to check
        
        Returns:
            True if team is recognized, False otherwise
        """
        if not team_name or team_name == "Unknown":
            return False
        
        # Check if normalizes to a different value (meaning it's in mapping)
        normalized = self.normalize(team_name)
        return normalized in self.mapping.values()
    
    def get_all_teams(self) -> list[str]:
        """Get list of all official team names.
        
        Returns:
            List of official CFL team names
        """
        # Get unique values from mapping (official names)
        return sorted(set(self.mapping.values()))


# Module-level convenience function
_normalizer_instance: Optional[TeamNormalizer] = None


def normalize_team_name(team_name: str) -> str:
    """Normalize team name using module-level singleton instance.
    
    This is a convenience function that maintains a single TeamNormalizer
    instance for efficiency.
    
    Args:
        team_name: Team name to normalize
    
    Returns:
        Normalized team name
    """
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = TeamNormalizer()
    return _normalizer_instance.normalize(team_name)


if __name__ == "__main__":
    # Test team normalization
    normalizer = TeamNormalizer()
    
    test_cases = [
        "Alouettes",
        "Montreal Alouettes",
        "Saskatchewan",
        "Roughriders",
        "Lions",
        "Unknown",
        "InvalidTeam"
    ]
    
    print("Team Name Normalization Tests:")
    print("=" * 50)
    for team in test_cases:
        normalized = normalizer.normalize(team)
        valid = normalizer.is_valid_team(team)
        print(f"{team:20} -> {normalized:30} (valid: {valid})")
