"""
Vision Agent - Agent 1

This agent analyzes images to extract team name and jersey number using
AWS Bedrock's vision-capable Claude model.
"""

import time
from typing import Dict, Any, Tuple

from strands_tools import image_reader
from strands.models import BedrockModel

from src.agents.base import BaseAgent
from src.models.telemetry import AgentTelemetry
from src.core.exceptions import VisionAnalysisError
from src.core.config import get_settings


class VisionAgent(BaseAgent):
    """Agent for extracting player information from images using computer vision."""
    
    def __init__(self, system_prompt: str):
        """Initialize vision agent.
        
        Args:
            system_prompt: System prompt for vision analysis
        """
        settings = get_settings()
        model = BedrockModel(model_id=settings.bedrock_model_id)
        
        super().__init__(
            model=model,
            system_prompt=system_prompt,
            tools=[image_reader],
            name="VisionAgent"
        )
    
    def execute(self, image_path: str) -> Tuple[Dict[str, Any], AgentTelemetry]:
        """Extract team name and jersey number from image.
        
        Args:
            image_path: Path to the player image
        
        Returns:
            Tuple of (vision_results_dict, telemetry)
        
        Raises:
            VisionAnalysisError: If vision analysis fails
        """
        self._log_execution_start(image_path=image_path)
        start_time = time.time()
        
        try:
            # Create agent and execute
            agent = self._create_agent_instance()
            result = agent(f"Can you describe this image: {image_path}")
            
            # Extract telemetry
            duration_ms = (time.time() - start_time) * 1000
            telemetry = self._extract_telemetry(result)
            telemetry.duration_ms = duration_ms
            
            # Parse response
            raw_response = str(result)
            self.logger.debug(f"Raw response (first 200 chars): {raw_response[:200]}")
            result_dict = self._parse_json_response(raw_response)
            
            # Validate response structure
            if "error" in result_dict:
                raise VisionAnalysisError(
                    f"Vision model returned error: {result_dict.get('reason', 'Unknown')}",
                    details=result_dict
                )
            
            self._log_execution_success(telemetry)
            return result_dict, telemetry
        
        except Exception as e:
            self._log_execution_error(e)
            if isinstance(e, VisionAnalysisError):
                raise
            raise VisionAnalysisError(f"Vision analysis failed: {str(e)}")
