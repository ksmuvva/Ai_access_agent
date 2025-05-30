"""
ADK-Based Accessibility Agent Framework
Using Google ADK Python framework for AI accessibility testing with A2A protocol support
"""

from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
from abc import abstractmethod

# Google ADK Python framework imports
from google.adk.agents import LlmAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.tools import custom_function

import os
import asyncio

class TestSeverity(Enum):
    """Accessibility test severity levels mapped to WCAG priority"""
    CRITICAL = "critical"     # Level A violations - critical accessibility barriers
    HIGH = "high"            # Level AA violations - significant barriers
    MEDIUM = "medium"        # Level AAA violations - minor barriers
    LOW = "low"             # Best practice recommendations
    INFO = "info"           # Informational findings

@dataclass
class AccessibilityIssue:
    """Represents an accessibility issue found during testing"""
    agent_name: str
    issue_type: str
    severity: TestSeverity
    description: str
    element_selector: Optional[str] = None
    wcag_guideline: Optional[str] = None
    suggested_fix: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None

class BaseAccessibilityAgent(LlmAgent):
    """
    ADK-based accessibility testing agent
    Inherits from Google ADK's LlmAgent for proper framework integration
    """
    
    def __init__(
        self, 
        name: str, 
        description: str,
        instructions: str,
        model: str = None,        tools: List = None,
        sub_agents: List = None
    ):
        """
        Initialize ADK-based accessibility agent
        
        Args:
            name: Agent identifier
            description: Agent's purpose and capabilities
            instructions: Detailed instructions for LLM behavior
            model: Claude model to use (default: claude-3-5-sonnet-20241022)
            tools: List of tools this agent can use
            sub_agents: Child agents for hierarchical coordination
        """
        if model is None:
            model = os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')
            
        super().__init__(
            name=name,
            description=description,
            instruction=instructions,
            model=model,
            tools=tools or [],
            sub_agents=sub_agents or []
        )
        
        # Initialize accessibility-specific attributes after LlmAgent initialization
        object.__setattr__(self, 'issues_found', [])
        object.__setattr__(self, 'agent_type', "accessibility_tester")
        
    async def analyze_accessibility(
        self, 
        url: str, 
        context: InvocationContext
    ) -> List[AccessibilityIssue]:
        """
        Analyze URL for accessibility issues using ADK framework
        
        Args:
            url: Target URL for accessibility testing
            context: ADK invocation context with session state
            
        Returns:
            List of accessibility issues found
        """
        # Store URL in session state for agent processing
        context.session.state['target_url'] = url
        context.session.state['wcag_version'] = '2.2'
        context.session.state['compliance_level'] = 'AA'
        
        # Execute the LLM agent to perform analysis
        events = []
        async for event in self._run_async_impl(context):
            events.append(event)
            
        # Extract issues from agent response or session state
        issues = context.session.state.get('accessibility_issues', [])
        
        # Convert to AccessibilityIssue objects if needed
        self.issues_found = self._parse_issues_from_response(issues, context)
        
        return self.issues_found
    
    def _parse_issues_from_response(
        self, 
        raw_issues: List[Dict], 
        context: InvocationContext
    ) -> List[AccessibilityIssue]:
        """
        Parse LLM response into structured AccessibilityIssue objects
        
        Args:
            raw_issues: Raw issue data from LLM response
            context: ADK invocation context
            
        Returns:
            List of structured AccessibilityIssue objects
        """
        parsed_issues = []
        
        for issue_data in raw_issues:
            if isinstance(issue_data, dict):
                issue = AccessibilityIssue(
                    agent_name=self.name,
                    issue_type=issue_data.get('issue_type', 'unknown'),
                    severity=TestSeverity(issue_data.get('severity', 'medium')),
                    description=issue_data.get('description', ''),
                    element_selector=issue_data.get('element_selector'),
                    wcag_guideline=issue_data.get('wcag_guideline'),
                    suggested_fix=issue_data.get('suggested_fix'),                    evidence=issue_data.get('evidence')
                )
                parsed_issues.append(issue)
                
        return parsed_issues
    
    @abstractmethod
    async def analyze(self, url: str, context: Dict[str, Any]) -> List[AccessibilityIssue]:
        """
        Analyze URL for accessibility issues - to be implemented by each agent
        
        Args:
            url: Target URL for accessibility testing
            context: Test context with configuration
            
        Returns:
            List of accessibility issues found
        """
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Return the capabilities and configuration of this agent
        
        Returns:
            Dictionary describing agent capabilities
        """
        pass
    
    async def validate_url(self, url: str) -> bool:
        """Validate if the URL is accessible and testable"""
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    return response.status == 200
        except Exception:            return False
    
    def add_issue(self, issue: AccessibilityIssue):
        """Add an accessibility issue to the agent's findings"""
        self.issues_found.append(issue)
    
    def get_issues_by_severity(self, severity: TestSeverity) -> List[AccessibilityIssue]:
        """Get issues filtered by severity level"""
        return [issue for issue in self.issues_found if issue.severity == severity]
    
    def clear_issues(self):
        """Clear all found issues (useful for new tests)"""
        self.issues_found.clear()

    # ADK-specific methods for proper framework integration
    async def _run_async_impl(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        ADK-required method for async execution
        Override in concrete agents for specific functionality
        """
        # Default implementation - concrete agents should override
        yield Event(
            event_type="agent_started",
            data={"agent_name": self.name, "url": context.session.state.get('target_url')}
        )
        
        # Perform analysis using legacy interface for backward compatibility
        url = context.session.state.get('target_url', '')
        if url:
            issues = await self.analyze(url, context.session.state)
            context.session.state['accessibility_issues'] = [
                {
                    'agent_name': issue.agent_name,
                    'issue_type': issue.issue_type,
                    'severity': issue.severity.value,
                    'description': issue.description,
                    'element_selector': issue.element_selector,
                    'wcag_guideline': issue.wcag_guideline,
                    'suggested_fix': issue.suggested_fix,
                    'evidence': issue.evidence
                }
                for issue in issues            ]
        
        yield Event(
            event_type="agent_completed",
            data={"agent_name": self.name, "issues_found": len(self.issues_found)}
        )
