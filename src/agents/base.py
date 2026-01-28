"""
Base Agent Class

This module provides the base class for all AI agents with common functionality
for JSON parsing, error handling, and telemetry tracking.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

from src.core.exceptions import AgentError, JSONParsingError
from src.models.telemetry import AgentTelemetry
from src.utils.json_parser import parse_json_response

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all AI agents.
    
    Provides common functionality:
    - JSON response parsing with error recovery
    - Telemetry tracking (tokens, duration)
    - Error handling and logging
    - Agent execution framework
    """
    
    def __init__(self, model, system_prompt: str, tools: list, name: str = "BaseAgent"):
        """Initialize base agent.
        
        Args:
            model: AI model instance (e.g., BedrockModel)
            system_prompt: System prompt for the agent
            tools: List of tools available to the agent
            name: Agent name for logging and telemetry
        """
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Tuple[Dict[str, Any], AgentTelemetry]:
        """Execute agent task.
        
        This method must be implemented by subclasses.
        
        Returns:
            Tuple of (result_dict, telemetry)
        """
        pass
    
    def _parse_json_response(self, raw_response: str) -> dict:
        """Parse JSON response with robust error recovery.
        
        Args:
            raw_response: Raw response string from agent
        
        Returns:
            Parsed JSON dictionary
        
        Raises:
            JSONParsingError: If JSON cannot be parsed
        """
        try:
            return parse_json_response(raw_response, context=self.name)
        except JSONParsingError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            raise
    
    def _extract_telemetry(self, result) -> AgentTelemetry:
        """Extract telemetry from agent result.
        
        Args:
            result: Agent execution result with metrics
        
        Returns:
            AgentTelemetry object
        """
        try:
            metrics = result.metrics.accumulated_usage
            return AgentTelemetry(
                agent_name=self.name,
                input_tokens=metrics.get('inputTokens', 0),
                output_tokens=metrics.get('outputTokens', 0),
                duration_ms=0  # Will be set by caller
            )
        except Exception as e:
            self.logger.warning(f"Failed to extract telemetry: {e}")
            return AgentTelemetry(
                agent_name=self.name,
                input_tokens=0,
                output_tokens=0,
                duration_ms=0
            )
    
    def _log_execution_start(self, **kwargs) -> None:
        """Log agent execution start."""
        params_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f"[{self.name}] Starting execution: {params_str}")
    
    def _log_execution_success(self, telemetry: AgentTelemetry) -> None:
        """Log successful agent execution."""
        self.logger.info(
            f"[{self.name}] Execution successful | "
            f"Input: {telemetry.input_tokens} tokens | "
            f"Output: {telemetry.output_tokens} tokens | "
            f"Duration: {telemetry.duration_ms:.0f}ms"
        )
    
    def _log_execution_error(self, error: Exception) -> None:
        """Log agent execution error."""
        self.logger.error(f"[{self.name}] Execution failed: {error}", exc_info=True)
    
    def _create_agent_instance(self):
        """Create agent instance with configured model, prompt, and tools.
        
        Returns:
            Agent instance ready for execution
        """
        from strands import Agent
        
        return Agent(
            system_prompt=self.system_prompt,
            tools=self.tools,
            model=self.model
        )
