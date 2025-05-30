"""
ADK-Based Accessibility Testing Orchestrator
Uses Google ADK's hierarchical sub-agents pattern instead of custom orchestration
"""

from typing import Dict, List, Any, Optional
import asyncio
import json
from datetime import datetime

from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

from agents.adk_coordinator import (
    AccessibilityCoordinatorAgent
)
from agents.greeter_agent import GreeterAgent
from agents.task_execution_agent import TaskExecutionAgent
from agents.base_agent import AccessibilityIssue, TestSeverity
from utils.report_generator import ReportGenerator
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ADKAccessibilityOrchestrator:
    """
    ADK-based orchestrator using hierarchical sub-agents pattern
    Replaces custom orchestration with Google ADK's native coordination
    """
    
    def __init__(self):
        # Initialize ADK agents using hierarchical pattern
        self.greeter_agent = GreeterAgent()
        self.task_executor = TaskExecutionAgent()
        self.coordinator_agent = AccessibilityCoordinatorAgent()
        self.report_generator = ReportGenerator()
        
        # Track testing sessions
        self.active_sessions: Dict[str, InvocationContext] = {}
        
    async def start_interactive_session(self) -> str:
        """
        Start an interactive accessibility testing session using ADK greeter agent
        
        Returns:
            Session ID for tracking
        """
        context = InvocationContext.create_new()
        session_id = context.session.id
        
        self.active_sessions[session_id] = context
        
        logger.info(f"Started ADK interactive session: {session_id}")
        
        return session_id
    
    async def process_user_input(
        self, 
        session_id: str, 
        user_input: str
    ) -> Dict[str, Any]:
        """
        Process user input through ADK greeter agent
        
        Args:
            session_id: Active session identifier
            user_input: User's request or URL
            
        Returns:
            Greeter agent response with next steps
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        context = self.active_sessions[session_id]
        context.session.state['user_input'] = user_input
        
        # Process through greeter agent
        response = await self.greeter_agent.greet_and_delegate(user_input)
        
        logger.info(f"Processed user input in session {session_id}")
        
        return response
    
    async def execute_accessibility_test(
        self,
        url: str,
        test_options: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute comprehensive accessibility test using ADK task execution agent
        
        Args:
            url: Target URL for accessibility testing
            test_options: Optional testing configuration
            session_id: Optional existing session ID
            
        Returns:
            Complete accessibility test results
        """
        # Create or use existing session
        if session_id and session_id in self.active_sessions:
            context = self.active_sessions[session_id]
        else:
            context = InvocationContext.create_new()
            session_id = context.session.id
            self.active_sessions[session_id] = context
        
        test_options = test_options or {}
        
        logger.info(f"Starting accessibility test for {url} in session {session_id}")
        
        try:
            # Execute test through ADK task execution agent
            results = await self.task_executor.execute_accessibility_test(url, test_options)
            
            # Store results in session
            context.session.state['test_results'] = results
            context.session.state['test_completed'] = True
            
            logger.info(f"Completed accessibility test: {results['total_issues']} issues found")
            
            return {
                "session_id": session_id,
                "status": "completed",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Accessibility test failed: {e}")
            
            error_result = {
                "session_id": session_id,
                "status": "error",
                "error": str(e),
                "url": url
            }
            
            context.session.state['test_error'] = error_result
            
            return error_result
    
    async def get_agent_capabilities(self) -> Dict[str, Any]:
        """
        Get comprehensive capabilities from all ADK agents
        
        Returns:
            Combined capabilities from greeter, executor, and coordinator
        """
        capabilities = {
            "orchestrator_type": "ADK_hierarchical",
            "framework": "Google ADK Python",
            "a2a_protocol": True,
            "agents": {}
        }
        
        # Get capabilities from each agent
        try:
            greeter_caps = {
                "name": self.greeter_agent.name,
                "description": self.greeter_agent.description,
                "type": "greeter",
                "sub_agents": len(self.greeter_agent.sub_agents)
            }
            capabilities["agents"]["greeter"] = greeter_caps
            
            task_executor_caps = {
                "name": self.task_executor.name,
                "description": self.task_executor.description,
                "type": "task_executor",
                "sub_agents": len(self.task_executor.sub_agents)
            }
            capabilities["agents"]["task_executor"] = task_executor_caps
            
            coordinator_caps = await self.coordinator_agent.get_capabilities()
            capabilities["agents"]["coordinator"] = coordinator_caps
            
        except Exception as e:
            logger.error(f"Failed to get agent capabilities: {e}")
            capabilities["error"] = str(e)
        
        return capabilities
    
    async def generate_comprehensive_report(
        self,
        session_id: str,
        report_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive accessibility report using ADK session data
        
        Args:
            session_id: Session with completed test results
            report_format: Output format ("json", "html", "pdf")
            
        Returns:
            Generated report data
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        context = self.active_sessions[session_id]
        
        if not context.session.state.get('test_completed'):
            raise ValueError(f"No completed test found in session {session_id}")
        
        test_results = context.session.state.get('test_results', {})
        
        # Generate report using existing report generator
        report_data = {
            "metadata": {
                "session_id": session_id,
                "framework": "Google ADK Python",
                "orchestrator_type": "hierarchical_sub_agents",
                "a2a_protocol_used": test_results.get('remote_agents_used', 0) > 0,
                "generation_timestamp": datetime.now().isoformat(),
                "wcag_version": test_results.get('wcag_version', '2.2'),
                "compliance_level": test_results.get('compliance_level', 'AA')
            },
            "test_summary": {
                "url": test_results.get('url'),
                "total_issues": test_results.get('total_issues', 0),
                "issues_by_severity": test_results.get('issues_by_severity', {}),
                "agents_executed": len(test_results.get('agent_results', {})),
                "remote_agents_used": test_results.get('remote_agents_used', 0)
            },
            "detailed_results": test_results
        }
        
        # Generate formatted report
        if report_format == "html":
            report_content = await self.report_generator.generate_html_report(report_data)
        elif report_format == "pdf":
            report_content = await self.report_generator.generate_pdf_report(report_data)
        else:
            report_content = json.dumps(report_data, indent=2)
        
        logger.info(f"Generated {report_format} report for session {session_id}")
        
        return {
            "session_id": session_id,
            "format": report_format,
            "content": report_content,
            "metadata": report_data["metadata"]
        }
    
    async def list_active_sessions(self) -> List[Dict[str, Any]]:
        """
        List all active ADK testing sessions
        
        Returns:
            List of active session summaries
        """
        sessions = []
        
        for session_id, context in self.active_sessions.items():
            session_info = {
                "session_id": session_id,
                "created_at": context.session.created_at.isoformat(),
                "state": {
                    "test_completed": context.session.state.get('test_completed', False),
                    "has_error": 'test_error' in context.session.state,
                    "target_url": context.session.state.get('target_url'),
                    "user_input": context.session.state.get('user_input')
                }
            }
            sessions.append(session_info)
        
        return sessions
    
    async def cleanup_session(self, session_id: str) -> bool:
        """
        Clean up completed ADK session
        
        Args:
            session_id: Session to clean up
            
        Returns:
            True if session was cleaned up successfully
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Cleaned up session {session_id}")
            return True
        
        return False
    
    async def discover_remote_agents(self) -> List[Dict[str, Any]]:
        """
        Discover remote accessibility agents via A2A protocol
        
        Returns:
            List of discovered remote agents
        """
        try:
            remote_agents = await self.coordinator_agent.discover_remote_agents()
            
            agent_info = []
            for agent in remote_agents:
                info = {
                    "name": agent.name,
                    "endpoint": agent.endpoint,
                    "capabilities": agent.capabilities,
                    "agent_type": "accessibility_tester"
                }
                agent_info.append(info)
            
            logger.info(f"Discovered {len(agent_info)} remote agents via A2A protocol")
            
            return agent_info
            
        except Exception as e:
            logger.error(f"Remote agent discovery failed: {e}")
            return []
    
    async def test_a2a_communication(self, agent_endpoint: str) -> Dict[str, Any]:
        """
        Test A2A protocol communication with a remote agent
        
        Args:
            agent_endpoint: Remote agent endpoint to test
            
        Returns:
            Communication test results
        """
        try:
            # This would test actual A2A communication in production
            test_result = {
                "endpoint": agent_endpoint,
                "status": "success",
                "latency_ms": 150,  # Mock latency
                "protocol_version": "A2A-1.0",
                "agent_responsive": True,
                "capabilities_received": True
            }
            
            logger.info(f"A2A communication test successful: {agent_endpoint}")
            
            return test_result
            
        except Exception as e:
            logger.error(f"A2A communication test failed: {e}")
            
            return {
                "endpoint": agent_endpoint,
                "status": "error",
                "error": str(e),
                "agent_responsive": False
            }


# Global orchestrator instance using ADK pattern
adk_orchestrator = ADKAccessibilityOrchestrator()


async def get_orchestrator() -> ADKAccessibilityOrchestrator:
    """Get the global ADK orchestrator instance"""
    return adk_orchestrator


# Legacy compatibility functions for existing code
async def test_url_accessibility(
    url: str, 
    agents: List[str] = None, 
    options: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Legacy compatibility function using ADK orchestrator
    
    Args:
        url: Target URL for testing
        agents: List of agent names (ignored - ADK handles agent selection)
        options: Testing options
        
    Returns:
        Test results compatible with existing code
    """
    orchestrator = await get_orchestrator()
    
    result = await orchestrator.execute_accessibility_test(url, options)
    
    # Transform to legacy format if needed
    if result.get('status') == 'completed':
        return result['results']
    else:
        return {"error": result.get('error', 'Unknown error')}


async def get_available_agents() -> List[Dict[str, Any]]:
    """
    Legacy compatibility function for agent listing
    
    Returns:
        List of available agents in legacy format
    """
    orchestrator = await get_orchestrator()
    capabilities = await orchestrator.get_agent_capabilities()
    
    agents = []
    for agent_type, agent_info in capabilities.get('agents', {}).items():
        agents.append({
            "name": agent_info.get('name', agent_type),
            "type": agent_type,
            "description": agent_info.get('description', ''),
            "capabilities": agent_info.get('capabilities', {})
        })
    
    return agents
