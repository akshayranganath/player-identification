"""
Player Data Models

This module defines data models for player information.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal

ConfidenceLevel = Literal["high", "medium", "low"]


@dataclass
class JerseyNumber:
    """Jersey number with confidence level."""
    value: str
    confidence: ConfidenceLevel
    
    def to_dict(self) -> dict:
        return {"value": self.value, "confidence": self.confidence}


@dataclass
class TeamInfo:
    """Team information with confidence level."""
    name: str
    colors_visible: list[str] = field(default_factory=list)
    confidence: ConfidenceLevel = "low"
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "colors_visible": self.colors_visible,
            "confidence": self.confidence
        }


@dataclass
class PlayerName:
    """Player name with confidence level."""
    value: str
    confidence: ConfidenceLevel
    
    def to_dict(self) -> dict:
        return {"value": self.value, "confidence": self.confidence}


@dataclass
class Player:
    """Complete player information."""
    
    player_id: int
    jersey_number: JerseyNumber
    team: TeamInfo
    player_name: Optional[PlayerName] = None
    visual_evidence: list[str] = field(default_factory=list)
    bounding_box: dict = field(default_factory=dict)
    overall_confidence: ConfidenceLevel = "low"
    web_search: Optional[dict] = None
    
    @property
    def high_confidence_count(self) -> int:
        """Count number of high-confidence fields."""
        count = 0
        if self.jersey_number.confidence == "high":
            count += 1
        if self.team.confidence == "high":
            count += 1
        if self.player_name and self.player_name.confidence == "high":
            count += 1
        return count
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if player has at least 2 high-confidence fields."""
        return self.high_confidence_count >= 2
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            "player_id": self.player_id,
            "jersey_number": self.jersey_number.to_dict(),
            "team": self.team.to_dict(),
            "visual_evidence": self.visual_evidence,
            "bounding_box": self.bounding_box,
            "overall_confidence": self.overall_confidence
        }
        
        if self.player_name:
            result["player_name"] = self.player_name.to_dict()
        
        if self.web_search:
            result["web_search"] = self.web_search
        
        return result


@dataclass
class VerifiedPlayer:
    """Verified player with database confirmation."""
    
    player_name: str
    player_team: str
    player_number: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "player_name": self.player_name,
            "player_team": self.player_team,
            "player_number": self.player_number
        }


@dataclass
class ImageAnalysis:
    """Image analysis metadata."""
    
    total_players_visible: int
    image_quality: Literal["excellent", "good", "fair", "poor"]
    viewing_angle: Literal["front", "side", "back", "overhead", "unclear"]
    
    def to_dict(self) -> dict:
        return {
            "total_players_visible": self.total_players_visible,
            "image_quality": self.image_quality,
            "viewing_angle": self.viewing_angle
        }
