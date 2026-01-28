"""
Telemetry Data Models

This module defines data models for tracking token usage and performance metrics.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class AgentTelemetry:
    """Telemetry data for a single agent execution."""
    
    agent_name: str
    input_tokens: int
    output_tokens: int
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def total_tokens(self) -> int:
        """Get total token count."""
        return self.input_tokens + self.output_tokens
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "agent_name": self.agent_name,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class CombinedTelemetry:
    """Combined telemetry for multiple agent executions."""
    
    agent_1: AgentTelemetry
    agent_2: AgentTelemetry
    additional_agents: list[AgentTelemetry] = field(default_factory=list)
    
    @property
    def total_input_tokens(self) -> int:
        """Get total input tokens across all agents."""
        total = self.agent_1.input_tokens + self.agent_2.input_tokens
        total += sum(a.input_tokens for a in self.additional_agents)
        return total
    
    @property
    def total_output_tokens(self) -> int:
        """Get total output tokens across all agents."""
        total = self.agent_1.output_tokens + self.agent_2.output_tokens
        total += sum(a.output_tokens for a in self.additional_agents)
        return total
    
    @property
    def total_tokens(self) -> int:
        """Get total tokens across all agents."""
        return self.total_input_tokens + self.total_output_tokens
    
    @property
    def total_duration_ms(self) -> float:
        """Get total duration across all agents."""
        total = self.agent_1.duration_ms + self.agent_2.duration_ms
        total += sum(a.duration_ms for a in self.additional_agents)
        return total
    
    def to_dict(self) -> dict:
        """Convert to dictionary format matching original structure."""
        return {
            "agent_1": {
                "input_tokens": self.agent_1.input_tokens,
                "output_tokens": self.agent_1.output_tokens
            },
            "agent_2": {
                "input_tokens": self.agent_2.input_tokens,
                "output_tokens": self.agent_2.output_tokens
            },
            "total": {
                "input_tokens": self.total_input_tokens,
                "output_tokens": self.total_output_tokens
            }
        }
