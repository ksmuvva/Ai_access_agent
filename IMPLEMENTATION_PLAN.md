# ADK & A2A Compliance Implementation Plan

## Phase 1: Standard Multi-Agent Pattern Implementation

### Current Issue
The official ADK documentation shows this standard pattern:

```python
# Define individual agents
greeter = LlmAgent(name="greeter", model="gemini-2.0-flash", ...)
task_executor = LlmAgent(name="task_executor", model="gemini-2.0-flash", ...)

# Create parent agent and assign children via sub_agents
coordinator = LlmAgent(
    name="Coordinator",
    model="gemini-2.0-flash",
    description="I coordinate greetings and tasks.",
    sub_agents=[ # Assign sub_agents here
        greeter,
        task_executor
    ]
)
```

### Implementation Strategy

1. **Create GreeterAgent** - Handles initial user interactions
2. **Create TaskExecutionAgent** - Manages accessibility testing tasks  
3. **Update AccessibilityCoordinatorAgent** - Follows standard pattern
4. **Preserve Accessibility Specialization** - Keep domain-specific agents as sub-agents

### File Updates Required

#### 1. Create `agents/greeter_agent.py`

```python
"""
ADK-compliant Greeter Agent for Accessibility Testing System
"""

from google.adk.agents import LlmAgent
import os

class AccessibilityGreeterAgent(LlmAgent):
    """
    Standard ADK greeter agent for accessibility testing interactions
    """
    
    def __init__(self):
        super().__init__(
            name="accessibility_greeter",
            model=os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022'),
            description="Friendly greeter for accessibility testing services",
            instruction="""
            You are a welcoming accessibility testing assistant. Your role is to:
            
            1. Greet users warmly and professionally
            2. Explain accessibility testing capabilities
            3. Guide users through available services
            4. Hand off to task execution agent for actual testing
            
            You specialize in WCAG 2.2 compliance testing and can help with:
            - Color contrast analysis
            - Keyboard navigation testing
            - Screen reader compatibility
            - Full accessibility audits
            
            Always be helpful, clear, and professional.
            """,
            tools=[],
            sub_agents=[]
        )
```

#### 2. Create `agents/task_execution_agent.py`

```python
"""
ADK-compliant Task Execution Agent for Accessibility Testing
"""

from google.adk.agents import LlmAgent
from google.adk.tools import custom_function
from google.adk.tools.tool_context import ToolContext
from typing import Dict, Any, List
import os

from .color_contrast_agent import ColorContrastAgent
from .keyboard_focus_agent import KeyboardFocusAgent

class AccessibilityTaskExecutionAgent(LlmAgent):
    """
    Task execution agent that coordinates accessibility testing
    """
    
    def __init__(self):
        # Initialize specialized accessibility agents as sub-agents
        accessibility_agents = [
            ColorContrastAgent(),
            KeyboardFocusAgent()
        ]
        
        super().__init__(
            name="accessibility_task_executor",
            model=os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022'),
            description="Executes accessibility testing tasks using specialized sub-agents",
            instruction="""
            You are the task execution coordinator for accessibility testing. Your role is to:
            
            1. Receive accessibility testing requests
            2. Break down complex tasks into specific test categories
            3. Coordinate with specialized accessibility agents
            4. Aggregate results into comprehensive reports
            5. Ensure WCAG 2.2 compliance validation
            
            Available specialized agents:
            - Color Contrast Agent: Analyzes color accessibility
            - Keyboard Focus Agent: Tests navigation accessibility
            
            Always provide detailed, actionable accessibility recommendations.
            """,
            tools=[self._create_testing_tools()],
            sub_agents=accessibility_agents
        )
    
    def _create_testing_tools(self):
        """Create ADK-compliant tools for accessibility testing"""
        
        @custom_function
        def run_accessibility_audit(url: str, test_types: List[str], context: ToolContext) -> Dict[str, Any]:
            """
            Coordinate comprehensive accessibility audit
            
            Args:
                url: Target URL for testing
                test_types: List of accessibility test types to perform
                context: ADK tool context
                
            Returns:
                Comprehensive accessibility test results
            """
            context.actions.skip_summarization = False
            
            # This would coordinate with sub-agents
            return {
                "url": url,
                "test_types": test_types,
                "status": "initiated",
                "coordinator": self.name
            }
        
        return [run_accessibility_audit]
```

#### 3. Update `agents/adk_coordinator.py`

```python
"""
Updated ADK Hierarchical Agent Coordinator - Standard Pattern Compliant
"""

import os
from typing import Dict, List, Any, Optional
from google.adk.agents import LlmAgent

from .greeter_agent import AccessibilityGreeterAgent
from .task_execution_agent import AccessibilityTaskExecutionAgent

class AccessibilityCoordinatorAgent(LlmAgent):
    """
    ADK-compliant coordinator following standard multi-agent pattern
    """
    
    def __init__(self):
        # Define individual agents per ADK standard pattern
        greeter = AccessibilityGreeterAgent()
        task_executor = AccessibilityTaskExecutionAgent()
        
        # Create parent agent and assign children via sub_agents
        super().__init__(
            name="accessibility_coordinator",
            model=os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022'),
            description="I coordinate accessibility testing greetings and tasks.",
            instruction="""
            You are the main coordinator for an accessibility testing system. 
            
            Your responsibilities:
            1. Route initial interactions to the greeter agent
            2. Direct testing tasks to the task execution agent
            3. Ensure smooth coordination between all agents
            4. Maintain session context and user preferences
            
            Standard workflow:
            1. Greeter handles initial user interaction
            2. Task executor performs accessibility testing
            3. You ensure seamless handoffs and context preservation
            
            Always maintain WCAG 2.2 compliance focus and professional accessibility expertise.
            """,
            tools=[],
            sub_agents=[  # Assign sub_agents here per ADK pattern
                greeter,
                task_executor
            ]
        )
```

## Phase 2: A2A Protocol Compliance

### Install Official A2A SDK

```bash
pip install a2a-python
```

### Create Agent Card Implementation

Create `agents/agent_card.py`:

```python
"""
A2A Agent Card Implementation for Accessibility Testing Agent
"""

from typing import Dict, Any, List

def create_accessibility_agent_card() -> Dict[str, Any]:
    """
    Create A2A compliant Agent Card for accessibility testing agent
    
    Returns:
        Agent Card compliant with A2A specification
    """
    return {
        "name": "AI Accessibility Testing Agent",
        "description": "Comprehensive WCAG 2.2 compliance testing agent using multi-agent coordination",
        "url": "http://localhost:8000/a2a/v1",
        "provider": {
            "organization": "Accessibility Testing Services",
            "url": "https://accessibility-testing.ai"
        },
        "version": "1.0.0",
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": False
        },
        "defaultInputModes": ["text/plain", "application/json"],
        "defaultOutputModes": ["application/json", "text/html"],
        "skills": [
            {
                "id": "wcag-compliance-testing",
                "name": "WCAG 2.2 Compliance Testing",
                "description": "Comprehensive accessibility testing for WCAG 2.2 AA compliance including color contrast, keyboard navigation, and screen reader compatibility",
                "tags": ["accessibility", "wcag", "compliance", "testing", "a11y"],
                "examples": [
                    "Test this website for WCAG 2.2 compliance",
                    "Analyze color contrast on https://example.com",
                    "Check keyboard navigation accessibility"
                ],
                "inputModes": ["text/plain", "application/json"],
                "outputModes": ["application/json", "text/html"]
            },
            {
                "id": "color-contrast-analysis",
                "name": "Color Contrast Analysis",
                "description": "Detailed color contrast ratio analysis for visual accessibility compliance",
                "tags": ["color", "contrast", "visual", "accessibility"],
                "examples": [
                    "Check color contrast ratios on this page",
                    "Analyze text readability for low vision users"
                ]
            },
            {
                "id": "keyboard-navigation-testing",
                "name": "Keyboard Navigation Testing", 
                "description": "Comprehensive keyboard accessibility and focus management testing",
                "tags": ["keyboard", "navigation", "focus", "accessibility"],
                "examples": [
                    "Test keyboard navigation on this form",
                    "Check focus indicators and tab order"
                ]
            }
        ],
        "supportsAuthenticatedExtendedCard": False
    }
```

### Update A2A Protocol Integration

Replace custom A2A implementation in `agents/a2a_protocol.py`:

```python
"""
Official A2A Protocol Integration for Accessibility Testing
"""

from a2a import A2AClient, A2AServer, AgentCard
from typing import Dict, Any, List, Optional
import asyncio
import json

from .agent_card import create_accessibility_agent_card

class A2AAccessibilityServer(A2AServer):
    """
    A2A Server implementation for accessibility testing agent
    """
    
    def __init__(self, coordinator_agent):
        self.coordinator_agent = coordinator_agent
        self.agent_card = create_accessibility_agent_card()
        super().__init__(agent_card=self.agent_card)
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming A2A messages
        
        Args:
            message: A2A protocol message
            
        Returns:
            A2A compliant response
        """
        # Integrate with ADK coordinator agent
        # This would invoke the coordinator agent with proper context
        response = await self.coordinator_agent.process_a2a_message(message)
        return response
    
    async def get_agent_card(self) -> Dict[str, Any]:
        """
        Return agent card for A2A discovery
        """
        return self.agent_card

class A2AAccessibilityClient:
    """
    A2A Client for discovering and communicating with remote accessibility agents
    """
    
    def __init__(self):
        self.client = A2AClient()
        self.discovered_agents = []
    
    async def discover_accessibility_agents(self) -> List[Dict[str, Any]]:
        """
        Discover remote accessibility testing agents
        
        Returns:
            List of discovered agent cards
        """
        # Use official A2A discovery mechanisms
        agents = await self.client.discover_agents(
            capabilities=["accessibility", "wcag", "testing"]
        )
        self.discovered_agents = agents
        return agents
    
    async def request_accessibility_test(
        self, 
        agent_url: str, 
        url: str,
        test_types: List[str]
    ) -> Dict[str, Any]:
        """
        Request accessibility testing from remote agent
        
        Args:
            agent_url: Target agent URL
            url: URL to test
            test_types: Types of accessibility tests to perform
            
        Returns:
            Test results from remote agent
        """
        message = {
            "role": "user",
            "parts": [{
                "type": "data",
                "data": {
                    "action": "accessibility_test",
                    "url": url,
                    "test_types": test_types,
                    "wcag_version": "2.2",
                    "compliance_level": "AA"
                }
            }],
            "messageId": f"test_request_{url.replace('://', '_').replace('/', '_')}"
        }
        
        response = await self.client.send_message(agent_url, message)
        return response
```

## Phase 3: Update Requirements and Dependencies

Update `requirements.txt`:

```txt
# Google ADK Python Framework
google-adk>=1.1.1

# Official A2A Protocol SDK  
a2a-python>=0.2.1

# Web automation and testing
playwright>=1.40.0
pytest>=7.4.0
pytest-asyncio>=0.21.0

# Accessibility testing libraries
axe-selenium-python>=2.1.6
colour>=0.1.5

# Web framework for A2A server
fastapi>=0.104.0
uvicorn>=0.24.0

# Async support
aiohttp>=3.9.0
asyncio-mqtt>=0.13.0

# Utilities
python-dotenv>=1.0.0
pydantic>=2.5.0
```

## Phase 4: Testing and Validation

Create `tests/test_adk_compliance.py`:

```python
"""
Test ADK Framework Compliance
"""

import pytest
from agents.adk_coordinator import AccessibilityCoordinatorAgent
from agents.greeter_agent import AccessibilityGreeterAgent
from agents.task_execution_agent import AccessibilityTaskExecutionAgent

def test_coordinator_has_standard_agents():
    """Test that coordinator follows standard ADK multi-agent pattern"""
    coordinator = AccessibilityCoordinatorAgent()
    
    # Verify sub_agents are configured
    assert hasattr(coordinator, 'sub_agents')
    assert len(coordinator.sub_agents) == 2
    
    # Verify agent types
    agent_names = [agent.name for agent in coordinator.sub_agents]
    assert "accessibility_greeter" in agent_names
    assert "accessibility_task_executor" in agent_names

def test_greeter_agent_initialization():
    """Test greeter agent proper initialization"""
    greeter = AccessibilityGreeterAgent()
    
    assert greeter.name == "accessibility_greeter"
    assert "claude" in greeter.model.lower()
    assert len(greeter.sub_agents) == 0  # Leaf agent

def test_task_executor_has_accessibility_agents():
    """Test task executor has accessibility-specific sub-agents"""
    executor = AccessibilityTaskExecutionAgent()
    
    assert executor.name == "accessibility_task_executor"
    assert len(executor.sub_agents) >= 2  # Should have color contrast and keyboard agents
    
    agent_names = [agent.name for agent in executor.sub_agents]
    assert any("color" in name.lower() for name in agent_names)
    assert any("keyboard" in name.lower() for name in agent_names)

@pytest.mark.asyncio
async def test_a2a_agent_card_creation():
    """Test A2A agent card creation"""
    from agents.agent_card import create_accessibility_agent_card
    
    card = create_accessibility_agent_card()
    
    # Verify required A2A fields
    assert "name" in card
    assert "description" in card
    assert "url" in card
    assert "version" in card
    assert "capabilities" in card
    assert "skills" in card
    
    # Verify accessibility-specific skills
    skill_ids = [skill["id"] for skill in card["skills"]]
    assert "wcag-compliance-testing" in skill_ids
```

## Implementation Timeline

### Week 1: Core ADK Compliance
- Day 1-2: Implement greeter and task execution agents
- Day 3: Update coordinator to follow standard pattern
- Day 4: Test and validate ADK compliance

### Week 2: A2A Integration  
- Day 1-2: Install and integrate official A2A SDK
- Day 3: Implement Agent Card and discovery
- Day 4: Test A2A protocol compliance

### Week 3: Integration and Testing
- Day 1-2: End-to-end testing
- Day 3: Performance optimization
- Day 4: Documentation and deployment prep

This plan ensures full compliance with both ADK Python framework and A2A protocol specifications while preserving the accessibility testing domain expertise.
