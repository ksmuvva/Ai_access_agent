"""
ADK Hierarchical Agent Coordinator
Main coordinator agent using Google ADK's hierarchical sub-agents pattern with A2A protocol support
"""

import os
from typing import Dict, List, Any, Optional, AsyncGenerator
from google.adk.agents import LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from .a2a_protocol import A2AProtocol, RemoteAgent
import asyncio
import json

from .base_agent import BaseAccessibilityAgent, AccessibilityIssue, TestSeverity
from .color_contrast_agent import ColorContrastAgent
from .keyboard_focus_agent import KeyboardFocusAgent
from .greeter_agent import GreeterAgent
from .task_execution_agent import TaskExecutionAgent


class AccessibilityCoordinatorAgent(BaseAccessibilityAgent):
    """
    ADK-based hierarchical coordinator agent for accessibility testing
    Uses standard ADK sub_agents pattern with greeter and task_executor
    """
    
    def __init__(self):
        # Create standard ADK agents following the official pattern
        greeter = GreeterAgent()
        task_executor = TaskExecutionAgent()
        
        super().__init__(
            name="accessibility_coordinator",
            description="Master coordinator for accessibility testing using standard ADK hierarchical sub-agents",
            instructions="""
            You are the main accessibility testing coordinator agent. Your responsibilities:
            
            1. COORDINATION: Manage sub-agents using standard ADK pattern (greeter + task_executor)
            2. WORKFLOW: Orchestrate greeter -> task_executor workflow for accessibility testing
            3. A2A PROTOCOL: Communicate with remote accessibility agents when available
            4. AGGREGATION: Collect and synthesize findings from all agents
            5. PRIORITIZATION: Rank issues by severity and WCAG compliance level
            6. REPORTING: Generate comprehensive accessibility reports
            
            Standard ADK workflow:
            1. Greeter agent handles user interaction and parses accessibility testing requests
            2. Task executor performs actual accessibility testing with specialized agents
            3. Coordinator aggregates results and generates reports
            
            For each URL analysis:
            - Route user requests through greeter agent for parsing
            - Delegate testing execution to task_executor agent
            - Coordinate with specialized accessibility agents (color contrast, keyboard focus)
            - Check for available remote agents via A2A protocol
            - Aggregate all findings into prioritized recommendations
              Always provide WCAG 2.2 guideline references and actionable fixes.
            """,
            model=os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022'),
            tools=[],
            sub_agents=[  # Assign sub_agents here - standard ADK pattern
                greeter,
                task_executor
            ]
        )
        
        # A2A Protocol setup for remote agent communication
        self.a2a_protocol = A2AProtocol()
        self.remote_agents: List[RemoteAgent] = []
        self.test_results: Dict[str, List[AccessibilityIssue]] = {}
        
    async def discover_remote_agents(self) -> List[RemoteAgent]:
        """
        Discover remote accessibility agents via A2A protocol
        
        Returns:
            List of discovered remote agents
        """
        try:
            # Discover agents in the accessibility testing network
            discovered = await self.a2a_protocol.discover_agents(
                agent_type="accessibility_tester",
                capabilities=["wcag_testing", "automated_accessibility"]
            )
            
            self.remote_agents = discovered
            return discovered
            
        except Exception as e:
            print(f"A2A discovery failed: {e}")
            return []
    
    async def coordinate_with_remote_agent(
        self, 
        remote_agent: RemoteAgent, 
        url: str,
        test_type: str
    ) -> List[AccessibilityIssue]:
        """
        Coordinate accessibility testing with a remote agent via A2A protocol
        
        Args:
            remote_agent: Remote agent to communicate with
            url: Target URL for testing
            test_type: Type of accessibility test to perform
            
        Returns:
            List of accessibility issues from remote agent
        """
        try:
            # Send testing request via A2A protocol
            response = await self.a2a_protocol.send_request(
                target_agent=remote_agent,
                action="analyze_accessibility",
                payload={
                    "url": url,
                    "test_type": test_type,
                    "wcag_version": "2.2",
                    "compliance_level": "AA"
                }
            )
            
            # Parse response into AccessibilityIssue objects
            issues = []
            if response.success and response.data:
                for issue_data in response.data.get('issues', []):
                    issue = AccessibilityIssue(
                        agent_name=f"remote_{remote_agent.name}",
                        issue_type=issue_data.get('issue_type', 'unknown'),
                        severity=TestSeverity(issue_data.get('severity', 'medium')),
                        description=issue_data.get('description', ''),
                        element_selector=issue_data.get('element_selector'),
                        wcag_guideline=issue_data.get('wcag_guideline'),
                        suggested_fix=issue_data.get('suggested_fix'),
                        evidence=issue_data.get('evidence')
                    )
                    issues.append(issue)
            
            return issues
            
        except Exception as e:
            print(f"A2A communication failed with {remote_agent.name}: {e}")
            return []
    
    async def analyze(self, url: str, context: Dict[str, Any]) -> List[AccessibilityIssue]:
        """
        Coordinate comprehensive accessibility analysis using sub-agents and A2A protocol
        
        Args:
            url: Target URL for accessibility testing
            context: Test context and configuration
            
        Returns:
            Aggregated list of accessibility issues from all agents
        """
        all_issues = []
        
        # 1. Discover and coordinate with remote agents via A2A protocol
        try:
            remote_agents = await self.discover_remote_agents()
            
            # Test with remote agents in parallel
            remote_tasks = []
            for agent in remote_agents:
                for test_type in ["color_contrast", "keyboard_navigation", "screen_reader", "form_validation"]:
                    task = self.coordinate_with_remote_agent(agent, url, test_type)
                    remote_tasks.append(task)
            
            if remote_tasks:
                remote_results = await asyncio.gather(*remote_tasks, return_exceptions=True)
                for result in remote_results:
                    if isinstance(result, list):
                        all_issues.extend(result)
                        
        except Exception as e:
            print(f"Remote agent coordination failed: {e}")
        
        # 2. Execute local sub-agents using ADK hierarchical pattern
        adk_context = InvocationContext.create_new()
        adk_context.session.state.update(context)
        adk_context.session.state['target_url'] = url
        
        # Execute each sub-agent
        for sub_agent in self.sub_agents:
            try:
                sub_agent_issues = await sub_agent.analyze_accessibility(url, adk_context)
                all_issues.extend(sub_agent_issues)
                
                # Store results by agent for reporting
                self.test_results[sub_agent.name] = sub_agent_issues
                
            except Exception as e:
                print(f"Sub-agent {sub_agent.name} failed: {e}")
        
        # 3. Aggregate and deduplicate issues
        unique_issues = self._deduplicate_issues(all_issues)
        
        # 4. Prioritize by severity and WCAG compliance level
        prioritized_issues = self._prioritize_issues(unique_issues)
        
        self.issues_found = prioritized_issues
        return prioritized_issues
    
    def _deduplicate_issues(self, issues: List[AccessibilityIssue]) -> List[AccessibilityIssue]:
        """
        Remove duplicate issues found by multiple agents
        
        Args:
            issues: List of accessibility issues potentially containing duplicates
            
        Returns:
            List of unique accessibility issues
        """
        seen = set()
        unique_issues = []
        
        for issue in issues:
            # Create a unique identifier for the issue
            issue_key = (
                issue.issue_type,
                issue.element_selector,
                issue.wcag_guideline,
                issue.description[:100]  # First 100 chars to handle slight variations
            )
            
            if issue_key not in seen:
                seen.add(issue_key)
                unique_issues.append(issue)
            else:
                # If duplicate found, keep the one with higher severity
                existing_issue = next(
                    (ui for ui in unique_issues 
                     if (ui.issue_type, ui.element_selector, ui.wcag_guideline, ui.description[:100]) == issue_key), 
                    None
                )
                if existing_issue and self._severity_rank(issue.severity) > self._severity_rank(existing_issue.severity):
                    unique_issues.remove(existing_issue)
                    unique_issues.append(issue)
        
        return unique_issues
    
    def _severity_rank(self, severity: TestSeverity) -> int:
        """Convert severity to numeric rank for comparison"""
        return {
            TestSeverity.CRITICAL: 5,
            TestSeverity.HIGH: 4,
            TestSeverity.MEDIUM: 3,
            TestSeverity.LOW: 2,
            TestSeverity.INFO: 1
        }.get(severity, 0)
    
    def _prioritize_issues(self, issues: List[AccessibilityIssue]) -> List[AccessibilityIssue]:
        """
        Prioritize issues by severity and WCAG compliance level
        
        Args:
            issues: List of accessibility issues to prioritize
            
        Returns:
            List of issues sorted by priority (highest first)
        """
        def priority_key(issue: AccessibilityIssue) -> tuple:
            severity_rank = self._severity_rank(issue.severity)
            
            # WCAG Level priority (A=3, AA=2, AAA=1)
            wcag_priority = 1
            if issue.wcag_guideline:
                if " A " in issue.wcag_guideline or issue.wcag_guideline.endswith(" A"):
                    wcag_priority = 3
                elif " AA " in issue.wcag_guideline or issue.wcag_guideline.endswith(" AA"):
                    wcag_priority = 2
            
            return (severity_rank, wcag_priority)
        
        return sorted(issues, key=priority_key, reverse=True)
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Return comprehensive capabilities of coordinator and sub-agents
        
        Returns:
            Dictionary describing all agent capabilities
        """
        capabilities = {
            "agent_type": "hierarchical_coordinator",
            "a2a_protocol_enabled": True,
            "wcag_compliance": "2.2",
            "supported_levels": ["A", "AA", "AAA"],
            "sub_agents": [],
            "remote_agents": len(self.remote_agents),
            "test_types": [
                "color_contrast",
                "keyboard_navigation", 
                "screen_reader_compatibility",
                "form_accessibility",
                "semantic_markup",
                "focus_management"
            ]
        }
        
        # Get capabilities from each sub-agent
        for sub_agent in self.sub_agents:
            sub_capabilities = await sub_agent.get_capabilities()
            capabilities["sub_agents"].append({
                "name": sub_agent.name,
                "capabilities": sub_capabilities
            })
        
        return capabilities
    
    async def _run_async_impl(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        ADK-required async execution method for coordinator agent
        
        Args:
            context: ADK invocation context
            
        Yields:
            Events describing coordination progress
        """
        yield Event(
            event_type="coordinator_started",
            data={
                "agent_name": self.name,
                "url": context.session.state.get('target_url'),
                "sub_agents": len(self.sub_agents)
            }
        )
        
        # Discover remote agents
        yield Event(
            event_type="a2a_discovery_started",
            data={"protocol": "A2A"}
        )
        
        remote_agents = await self.discover_remote_agents()
        
        yield Event(
            event_type="a2a_discovery_completed",
            data={"remote_agents_found": len(remote_agents)}
        )
        
        # Execute sub-agents using ADK hierarchical pattern
        for sub_agent in self.sub_agents:
            yield Event(
                event_type="sub_agent_started",
                data={"sub_agent_name": sub_agent.name}
            )
            
            # Execute sub-agent and collect its events
            async for sub_event in sub_agent._run_async_impl(context):
                # Forward sub-agent events with coordinator context
                yield Event(
                    event_type=f"sub_agent_{sub_event.event_type}",
                    data={
                        "coordinator": self.name,
                        "sub_agent": sub_agent.name,
                        **sub_event.data
                    }
                )
            
            yield Event(
                event_type="sub_agent_completed",
                data={"sub_agent_name": sub_agent.name}
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
                for issue in issues
            ]
        
        yield Event(
            event_type="coordinator_completed",
            data={
                "agent_name": self.name,
                "total_issues": len(self.issues_found),
                "sub_agents_executed": len(self.sub_agents),
                "remote_agents_used": len(self.remote_agents)
            }
        )


class GreeterAgent(LlmAgent):
    """
    ADK Greeter Agent for initial user interaction and task delegation
    Entry point for accessibility testing workflow
    """
    
    def __init__(self):
        super().__init__(
            name="accessibility_greeter",
            description="Initial interaction agent for accessibility testing workflow",
            instruction="""
            You are the accessibility testing greeter agent. Welcome users and help them start accessibility testing.
            
            Your responsibilities:            1. Welcome users to the accessibility testing system
            2. Gather requirements (URL, test scope, WCAG level)
            3. Delegate to the coordinator agent for execution
            4. Provide initial guidance on accessibility best practices
            
            Be friendly, helpful, and explain the testing process clearly.
            """,
            model=os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022'),
            tools=[],
            sub_agents=[AccessibilityCoordinatorAgent()]
        )
    
    async def greet_and_delegate(self, user_input: str) -> Dict[str, Any]:
        """
        Process user greeting and delegate to coordinator
        
        Args:
            user_input: User's initial request
            
        Returns:
            Response with greeting and coordination setup
        """
        context = InvocationContext.create_new()
        context.session.state['user_input'] = user_input
        
        # Extract URL and requirements from user input
        # This would typically use LLM parsing in production
        response = {
            "greeting": f"Welcome to the AI Accessibility Testing Agent! I'll help you test '{user_input}' for WCAG 2.2 compliance.",
            "status": "ready",
            "coordinator_available": True,
            "next_steps": [
                "URL validation",
                "Sub-agent coordination", 
                "Remote agent discovery",
                "Comprehensive accessibility analysis"
            ]
        }
        
        return response


class TaskExecutionAgent(LlmAgent):
    """
    ADK Task Execution Agent for managing accessibility testing workflows
    Coordinates between greeter and coordinator agents
    """
    
    def __init__(self):
        super().__init__(
            name="accessibility_task_executor",
            description="Task execution agent for accessibility testing workflows",
            instruction="""
            You are the accessibility testing task execution agent. You coordinate testing workflows.
            
            Your responsibilities:
            1. Receive delegated tasks from the greeter agent
            2. Validate URLs and testing parameters
            3. Execute comprehensive testing via the coordinator agent
            4. Format and return results to users
            5. Handle error cases and provide helpful feedback            
            Ensure all testing follows WCAG 2.2 guidelines and provides actionable results.
            """,
            model=os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022'),
            tools=[],
            sub_agents=[AccessibilityCoordinatorAgent()]
        )
    
    async def execute_accessibility_test(
        self, 
        url: str, 
        test_options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute comprehensive accessibility test
        
        Args:
            url: Target URL for testing
            test_options: Optional testing configuration
            
        Returns:
            Complete test results and recommendations
        """
        test_options = test_options or {}
        
        context = InvocationContext.create_new()
        context.session.state.update({
            'target_url': url,
            'wcag_version': test_options.get('wcag_version', '2.2'),
            'compliance_level': test_options.get('compliance_level', 'AA'),
            'include_remote_agents': test_options.get('include_remote_agents', True)
        })
        
        # Execute coordinator agent
        coordinator = self.sub_agents[0]  # AccessibilityCoordinatorAgent
        issues = await coordinator.analyze_accessibility(url, context)
        
        # Format results
        results = {
            "url": url,
            "test_timestamp": context.session.created_at.isoformat(),
            "wcag_version": "2.2",
            "compliance_level": test_options.get('compliance_level', 'AA'),
            "total_issues": len(issues),
            "issues_by_severity": {
                "critical": len([i for i in issues if i.severity == TestSeverity.CRITICAL]),
                "high": len([i for i in issues if i.severity == TestSeverity.HIGH]),
                "medium": len([i for i in issues if i.severity == TestSeverity.MEDIUM]),
                "low": len([i for i in issues if i.severity == TestSeverity.LOW]),
                "info": len([i for i in issues if i.severity == TestSeverity.INFO])
            },
            "issues": [
                {
                    "agent": issue.agent_name,
                    "type": issue.issue_type,
                    "severity": issue.severity.value,
                    "description": issue.description,
                    "element": issue.element_selector,
                    "wcag_guideline": issue.wcag_guideline,
                    "fix": issue.suggested_fix,
                    "evidence": issue.evidence
                }
                for issue in issues
            ],
            "agent_results": coordinator.test_results,
            "remote_agents_used": len(coordinator.remote_agents)
        }
        
        return results
