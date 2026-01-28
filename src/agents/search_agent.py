"""
Search Agent - Agent 2

This agent uses web search to find player names based on team and jersey number.
"""

import time
from typing import Dict, Any, Tuple

from strands.models import BedrockModel

from src.agents.base import BaseAgent
from src.models.telemetry import AgentTelemetry
from src.core.exceptions import WebSearchError
from src.core.config import get_settings
from src.tools.web_search import web_search_tool


class SearchAgent(BaseAgent):
    """Agent for finding player names using web search."""
    
    def __init__(self, system_prompt: str):
        """Initialize search agent.
        
        Args:
            system_prompt: System prompt for player search
        """
        settings = get_settings()
        model = BedrockModel(model_id=settings.bedrock_model_id)
        
        super().__init__(
            model=model,
            system_prompt=system_prompt,
            tools=[web_search_tool],
            name="SearchAgent"
        )
    
    def execute(self, team_name: str, jersey_number: str) -> Tuple[Dict[str, Any], AgentTelemetry]:
        """Find player name based on team and jersey number.
        
        Args:
            team_name: Name of the CFL team
            jersey_number: Player's jersey number
        
        Returns:
            Tuple of (search_results_dict, telemetry)
        
        Raises:
            WebSearchError: If web search fails
        """
        self._log_execution_start(team=team_name, number=jersey_number)
        start_time = time.time()
        
        # Handle case where SERP API key is missing
        settings = get_settings()
        if not settings.serp_api_key or settings.serp_api_key == "your_serpapi_key_here":
            self.logger.error("SERP_API_KEY not configured")
            return {
                "player_name": "Unknown",
                "confidence": "low",
                "error": "SERP_API_KEY not found in environment variables",
                "reasoning": "Cannot perform web search without API key",
                "sources": []
            }, AgentTelemetry(
                agent_name=self.name,
                input_tokens=0,
                output_tokens=0,
                duration_ms=0
            )
        
        try:
            # Create agent and execute
            agent = self._create_agent_instance()
            query = f"Find the name of the CFL player who plays for {team_name} and wears jersey number {jersey_number}"
            
            self.logger.debug(f"Search query: {query}")
            result = agent(query)
            
            # Extract telemetry
            duration_ms = (time.time() - start_time) * 1000
            telemetry = self._extract_telemetry(result)
            telemetry.duration_ms = duration_ms
            
            # Parse response
            raw_response = str(result)
            self.logger.debug(f"Raw response: {raw_response[:200]}...")
            result_dict = self._parse_json_response(raw_response)
            
            # Ensure all expected fields are present
            result_dict.setdefault("player_name", "Unknown")
            result_dict.setdefault("confidence", "low")
            result_dict.setdefault("reasoning", "No reasoning provided")
            result_dict.setdefault("sources", [])
            
            self.logger.debug(
                f"Search result: {result_dict['player_name']} "
                f"(confidence: {result_dict['confidence']})"
            )
            
            self._log_execution_success(telemetry)
            return result_dict, telemetry
        
        except Exception as e:
            self._log_execution_error(e)
            
            # Return fallback result instead of raising
            duration_ms = (time.time() - start_time) * 1000
            return {
                "player_name": "Unknown",
                "confidence": "low",
                "error": str(e),
                "reasoning": "An error occurred during the search",
                "sources": []
            }, AgentTelemetry(
                agent_name=self.name,
                input_tokens=0,
                output_tokens=0,
                duration_ms=duration_ms
            )
