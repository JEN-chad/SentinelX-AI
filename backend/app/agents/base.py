"""SentinelX AI - Base Agent Interface

Abstract base class defining standardized agent contracts, execution traces,
and strict action-catalogue validation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from app.schemas.agents import AgentRunResult, AgentTask
from app.schemas.common import AgentName


class BaseAgent(ABC):
    """Abstract base contract for all specialized SentinelX agents."""

    def __init__(self, agent_name: AgentName, version: str = "1.0.0"):
        self.agent_name = agent_name
        self.version = version

    @abstractmethod
    def run(self, task: AgentTask, context: Dict[str, Any]) -> AgentRunResult:
        """Execute agent analysis on a given task and context.
        
        Args:
            task: Validated task payload with incident ID and parameters.
            context: Shared execution context (e.g., event records, detections).
            
        Returns:
            Validated AgentRunResult instance.
        """
        pass
