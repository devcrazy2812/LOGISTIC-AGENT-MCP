import time
from typing import List, Dict, Any, Optional
from ..models.entities import AgentThought

class BaseAgent:
    """
    Base Autonomous Agent implementing ReAct (Reasoning + Acting)
    and structured Chain-of-Thought communication.
    """

    def __init__(self, name: str, role: str, color: str = "#3b82f6"):
        self.name = name
        self.role = role
        self.color = color
        self.thoughts: List[AgentThought] = []

    def record_thought(self, phase: str, content: str, tools_used: Optional[List[str]] = None) -> AgentThought:
        thought = AgentThought(
            agent_name=self.name,
            role=self.role,
            phase=phase,
            content=content,
            timestamp=time.strftime("%H:%M:%S"),
            tools_used=tools_used or []
        )
        self.thoughts.append(thought)
        return thought

    def clear_thoughts(self):
        self.thoughts = []
