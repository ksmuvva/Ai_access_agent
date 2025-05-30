"""
ADK Agent Registry
Manages accessibility testing agents using Google ADK hierarchical architecture
"""

from typing import Dict, List, Type
from .base_agent import BaseAccessibilityAgent
from .keyboard_focus_agent import KeyboardFocusAgent
from .color_contrast_agent import ColorContrastAgent
from .adk_coordinator import (
    AccessibilityCoordinatorAgent,
    GreeterAgent, 
    TaskExecutionAgent
)
from .a2a_protocol import A2AProtocol, RemoteAgent

class ADKAgentRegistry:
    """ADK-based registry for managing accessibility testing agents"""
    
    def __init__(self):
        self._agents: Dict[str, Type[BaseAccessibilityAgent]] = {}
        self._adk_agents: Dict[str, object] = {}
        self._register_default_agents()
        self._register_adk_agents()
    
    def _register_default_agents(self):
        """Register the default set of sub-agents"""
        self.register_agent('keyboard-focus', KeyboardFocusAgent)
        self.register_agent('color-contrast', ColorContrastAgent)
    
    def register_agent(self, agent_id: str, agent_class: Type[BaseAccessibilityAgent]):
        """Register a new agent class"""
        self._agents[agent_id] = agent_class
    
    def get_agent(self, agent_id: str) -> BaseAccessibilityAgent:
        """Get an instance of the specified agent"""
        if agent_id not in self._agents:
            raise ValueError(f"Agent '{agent_id}' not found in registry")
        
        return self._agents[agent_id]()
    
    def get_all_agents(self) -> List[BaseAccessibilityAgent]:
        """Get instances of all registered agents"""
        return [agent_class() for agent_class in self._agents.values()]
    
    def list_agent_ids(self) -> List[str]:
        """Get list of all registered agent IDs"""
        return list(self._agents.keys())
    
    def get_agent_info(self, agent_id: str) -> Dict:
        """Get information about a specific agent"""
        if agent_id not in self._agents:
            raise ValueError(f"Agent '{agent_id}' not found in registry")
        
        agent = self._agents[agent_id]()
        return {
            'id': agent_id,
            'name': agent.name,
            'description': agent.description
        }
    
    def _register_adk_agents(self):
        """Register ADK hierarchical agents"""
        self._adk_agents['coordinator'] = AccessibilityCoordinatorAgent
        self._adk_agents['greeter'] = GreeterAgent
        self._adk_agents['task_executor'] = TaskExecutionAgent
    
    def get_adk_agent(self, agent_type: str):
        """Get an ADK agent instance"""
        if agent_type not in self._adk_agents:
            raise ValueError(f"ADK agent '{agent_type}' not found")
        
        return self._adk_agents[agent_type]()
    
    def get_coordinator_agent(self) -> AccessibilityCoordinatorAgent:
        """Get the main ADK coordinator agent"""
        return self.get_adk_agent('coordinator')
    
    def get_greeter_agent(self) -> GreeterAgent:
        """Get the ADK greeter agent"""
        return self.get_adk_agent('greeter')
    
    def get_task_executor_agent(self) -> TaskExecutionAgent:
        """Get the ADK task executor agent"""
        return self.get_adk_agent('task_executor')
    
    def list_adk_agents(self) -> List[str]:
        """List all available ADK agents"""
        return list(self._adk_agents.keys())
    
    def get_a2a_protocol(self) -> A2AProtocol:
        """Get A2A protocol instance for remote agent communication"""
        return A2AProtocol()

# Global ADK agent registry instance
adk_registry = ADKAgentRegistry()

# Legacy compatibility
registry = adk_registry  # For backward compatibility with existing code

# Export all agent classes and utilities
__all__ = [
    'BaseAccessibilityAgent',
    'KeyboardFocusAgent', 
    'ColorContrastAgent',
    'AccessibilityCoordinatorAgent',
    'GreeterAgent',
    'TaskExecutionAgent',
    'A2AProtocol',
    'RemoteAgent',
    'ADKAgentRegistry',
    'adk_registry',
    'registry'  # Legacy compatibility
]
