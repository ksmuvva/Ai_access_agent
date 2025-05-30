"""
Mock Google ADK classes for demonstration purposes
Since google-adk may not be available in the environment, we'll create mock classes
that demonstrate the ADK patterns without requiring the actual package
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import uuid
from datetime import datetime

class LlmAgent:
    """Mock LlmAgent class that simulates Google ADK's LlmAgent"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        instruction: str = "",
        model: str = "claude-3-5-sonnet-20241022",
        tools: List = None,
        sub_agents: List = None
    ):
        self.name = name
        self.description = description
        self.instruction = instruction
        self.model = model
        self.tools = tools or []
        self.sub_agents = sub_agents or []
        self.agent_id = str(uuid.uuid4())
        
    async def invoke(self, message: str, context: Dict = None) -> Dict:
        """Mock invoke method"""
        return {
            "response": f"Mock response from {self.name}: {message}",
            "agent": self.name,
            "timestamp": datetime.now().isoformat()
        }

class BaseAgent:
    """Mock BaseAgent class"""
    
    def __init__(self, name: str):
        self.name = name
        self.agent_id = str(uuid.uuid4())

@dataclass
class InvocationContext:
    """Mock InvocationContext class"""
    session_id: str
    state: Dict[str, Any]
    
    @classmethod
    def create_new(cls):
        return cls(
            session_id=str(uuid.uuid4()),
            state={}
        )

@dataclass  
class Event:
    """Mock Event class"""
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
