"""
Player Identification Service

This module orchestrates the player identification workflow using multiple agents.
"""

import logging
from typing import List, Tuple

from src.agents.vision_agent import VisionAgent
from src.agents.search_agent import SearchAgent
from src.repositories.player_repository import PlayerRepository
from src.models.player import VerifiedPlayer
from src.models.telemetry import CombinedTelemetry, AgentTelemetry
from src.utils.team_normalizer import normalize_team_name
from src.core.constants import MIN_HIGH_CONFIDENCE_FIELDS
from src.core.config import get_settings

logger = logging.getLogger(__name__)


class PlayerIdentificationService:
    """Service for identifying CFL players from images."""
    
    def __init__(
        self,
        vision_agent: VisionAgent,
        search_agent: SearchAgent,
        player_repository: PlayerRepository
    ):
        """Initialize player identification service.
        
        Args:
            vision_agent: Agent for image analysis
            search_agent: Agent for player name search
            player_repository: Repository for player data
        """
        self.vision_agent = vision_agent
        self.search_agent = search_agent
        self.player_repository = player_repository
    
    def identify_players(
        self,
        image_path: str
    ) -> Tuple[List[VerifiedPlayer], CombinedTelemetry]:
        """Identify and verify players in image.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Tuple of (verified_players list, telemetry)
        """
        logger.info(f"{'='*60}")
        logger.info(f"Processing image: {image_path}")
        logger.info(f"{'='*60}")
        
        # Agent 1: Extract team and jersey number
        logger.info("[Agent 1] Extracting team name and jersey number from image...")
        vision_results, agent_1_telemetry = self.vision_agent.execute(image_path)
        
        if "error" in vision_results:
            logger.error(f"[Agent 1] Error: {vision_results['error']}")
            return [], self._create_empty_telemetry(agent_1_telemetry)
        
        logger.info("[Agent 1] Extraction complete!")
        
        # Process each player found in the image
        verified_players = []
        agent_2_combined_telemetry = AgentTelemetry(
            agent_name="SearchAgent",
            input_tokens=0,
            output_tokens=0,
            duration_ms=0
        )
        
        if "players" in vision_results:
            for player in vision_results["players"]:
                player_id = player.get("player_id", "Unknown")
                team_name = player.get("team", {}).get("name", "Unknown")
                jersey_number = player.get("jersey_number", {}).get("value", "-1")
                
                logger.info(
                    f"[Agent 2] Searching for player {player_id}: "
                    f"Team={team_name}, Jersey={jersey_number}"
                )
                
                # Agent 2: Search for player name
                if team_name != "Unknown" and jersey_number != "-1":
                    search_results, agent_2_telemetry = self.search_agent.execute(
                        team_name, jersey_number
                    )
                    
                    # Accumulate telemetry
                    agent_2_combined_telemetry.input_tokens += agent_2_telemetry.input_tokens
                    agent_2_combined_telemetry.output_tokens += agent_2_telemetry.output_tokens
                    agent_2_combined_telemetry.duration_ms += agent_2_telemetry.duration_ms
                    
                    # Add player_name field to player dict
                    player["player_name"] = {
                        "value": search_results.get("player_name", "Unknown"),
                        "confidence": search_results.get("confidence", "low")
                    }
                    player["web_search"] = search_results
                    
                    logger.info(
                        f"[Agent 2] Found: {player['player_name']['value']} "
                        f"(confidence: {player['player_name']['confidence']})"
                    )
                else:
                    player["player_name"] = {"value": "Unknown", "confidence": "low"}
                    player["web_search"] = {
                        "player_name": "Unknown",
                        "confidence": "low",
                        "error": "Insufficient information",
                        "reasoning": "Team name or jersey number not available",
                        "sources": []
                    }
                    logger.info("[Agent 2] Skipped - insufficient information")
        
        # Filter high confidence players
        filtered_players = self._filter_high_confidence_players(vision_results)
        logger.info(f"Filtered {len(filtered_players)} high-confidence players")
        
        # Verify against database
        verified_players = self._verify_players_in_database(filtered_players)
        logger.info(f"Verified {len(verified_players)} players against database")
        
        # Create combined telemetry
        telemetry = CombinedTelemetry(
            agent_1=agent_1_telemetry,
            agent_2=agent_2_combined_telemetry
        )
        
        return verified_players, telemetry
    
    def _filter_high_confidence_players(self, result: dict) -> List[dict]:
        """Filter players with at least 2 high-confidence fields."""
        filtered_players = []
        
        if "error" in result:
            return filtered_players
        
        players = result.get("players", [])
        
        for player in players:
            high_confidence_count = 0
            player_info = {
                "player_name": None,
                "player_team": None,
                "player_number": None
            }
            
            # Check each field for high confidence
            if "player_name" in player and player["player_name"].get("confidence") == "high":
                high_confidence_count += 1
                player_info["player_name"] = player["player_name"].get("value")
            
            if "jersey_number" in player and player["jersey_number"].get("confidence") == "high":
                high_confidence_count += 1
                player_info["player_number"] = player["jersey_number"].get("value")
            
            if "team" in player and player["team"].get("confidence") == "high":
                high_confidence_count += 1
                raw_team_name = player["team"].get("name")
                player_info["player_team"] = normalize_team_name(raw_team_name)
            
            # Only include if at least 2 parameters have high confidence
            if high_confidence_count >= MIN_HIGH_CONFIDENCE_FIELDS:
                # Fill in missing values
                if player_info["player_name"] is None:
                    player_info["player_name"] = player.get("player_name", {}).get("value", "Unknown")
                
                if player_info["player_number"] is None:
                    player_info["player_number"] = player.get("jersey_number", {}).get("value", "Unknown")
                
                if player_info["player_team"] is None:
                    raw_team_name = player.get("team", {}).get("name", "Unknown")
                    player_info["player_team"] = normalize_team_name(raw_team_name)
                
                filtered_players.append(player_info)
                logger.info(f"Filtered player (high_confidence_count={high_confidence_count}): {player_info}")
            else:
                logger.debug(
                    f"Player skipped: only {high_confidence_count} high-confidence fields "
                    f"(need {MIN_HIGH_CONFIDENCE_FIELDS}+)"
                )
        
        return filtered_players
    
    def _verify_players_in_database(self, filtered_players: List[dict]) -> List[VerifiedPlayer]:
        """Verify filtered players exist in database."""
        verified_players = []
        
        for player in filtered_players:
            team = player.get("player_team")
            number = player.get("player_number")
            name = player.get("player_name")
            
            logger.debug(f"Verifying player: team={team}, number={number}, name={name}")
            
            # Skip if essential fields are Unknown
            if not team or team == "Unknown" or not number or number == "Unknown":
                logger.debug(f"Skipped - missing essential fields")
                continue
            
            # Verify in database
            db_name = self.player_repository.find_by_team_and_number(team, str(number))
            
            if db_name:
                # If name is Unknown, use database name
                if name == "Unknown" or not name:
                    logger.info(f"Updated player name from database: '{name}' -> '{db_name}'")
                    name = db_name
                
                verified_player = VerifiedPlayer(
                    player_name=name,
                    player_team=team,
                    player_number=str(number)
                )
                verified_players.append(verified_player)
                logger.info(f"Verified player in database: {verified_player.to_dict()}")
            else:
                logger.warning(
                    f"Player not found in database: team={team}, number={number}"
                )
        
        return verified_players
    
    def _create_empty_telemetry(self, agent_1_telemetry: AgentTelemetry) -> CombinedTelemetry:
        """Create empty telemetry for error cases."""
        return CombinedTelemetry(
            agent_1=agent_1_telemetry,
            agent_2=AgentTelemetry(
                agent_name="SearchAgent",
                input_tokens=0,
                output_tokens=0,
                duration_ms=0
            )
        )
