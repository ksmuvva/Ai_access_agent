"""
Task Execution Agent - Standard ADK Pattern
Executes accessibility testing tasks coordinated by greeter agent
"""

from typing import Dict, List, Any, Optional
from google.adk.agents import LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.tools import custom_function
import asyncio

from .base_agent import AccessibilityIssue, TestSeverity
from .color_contrast_agent import ColorContrastAgent
from .keyboard_focus_agent import KeyboardFocusAgent


class TaskExecutionAgent(LlmAgent):
    """
    Standard ADK Task Execution Agent for accessibility testing
    Executes testing tasks and coordinates with specialized agents
    """
    
    def __init__(self):
        # Initialize specialized accessibility agents
        self.color_contrast_agent = ColorContrastAgent()
        self.keyboard_focus_agent = KeyboardFocusAgent()
        
        super().__init__(
            name="task_executor",
            model="claude-3-5-sonnet-20241022",  # User requested Claude
            description="Task execution agent for accessibility testing operations",
            instruction="""
            You are the task execution agent for accessibility testing. Your responsibilities:
            
            1. Execute accessibility testing tasks delegated by the greeter agent
            2. Coordinate with specialized accessibility testing agents
            3. Manage test execution workflow and timing
            4. Aggregate results from multiple testing agents
            5. Generate comprehensive accessibility reports
            
            For each testing task:
            - Validate the target URL is accessible
            - Coordinate with appropriate specialized agents
            - Monitor test execution progress
            - Compile results into actionable recommendations
            - Ensure WCAG 2.2 compliance mapping
            
            Always prioritize critical accessibility barriers and provide specific fix recommendations.
            """,
            tools=[self._get_execution_tools()]
        )
    
    def _get_execution_tools(self) -> List:
        """Get tools available to the task execution agent"""
        return [
            self.execute_accessibility_test,
            self.validate_url,
            self.compile_test_results
        ]
    
    @custom_function
    def validate_url(self, url: str) -> Dict[str, Any]:
        """
        Validate that the target URL is accessible for testing
        
        Args:
            url: Target URL to validate
            
        Returns:
            Validation results
        """
        import requests
        from urllib.parse import urlparse
        
        try:
            # Parse URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {
                    "valid": False,
                    "error": "Invalid URL format",
                    "url": url
                }
            
            # Check if URL is accessible
            response = requests.head(url, timeout=10, allow_redirects=True)
            
            return {
                "valid": response.status_code < 400,
                "status_code": response.status_code,
                "url": url,
                "final_url": response.url if response.url != url else url
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "url": url
            }
    
    @custom_function
    def execute_accessibility_test(
        self, 
        url: str, 
        test_types: List[str] = None,
        wcag_level: str = "AA"
    ) -> Dict[str, Any]:
        """
        Execute comprehensive accessibility testing
        
        Args:
            url: Target URL for testing
            test_types: List of test types to execute
            wcag_level: WCAG compliance level (A, AA, AAA)
            
        Returns:
            Compiled test results
        """
        if test_types is None:
            test_types = ["all"]
        
        # Validate URL first
        validation = self.validate_url(url)
        if not validation["valid"]:
            return {
                "success": False,
                "error": f"URL validation failed: {validation['error']}",
                "url": url
            }
        
        test_results = {
            "url": url,
            "wcag_level": wcag_level,
            "test_types": test_types,
            "issues": [],
            "summary": {},
            "timestamp": None
        }
        
        # Execute requested tests
        try:
            from datetime import datetime
            test_results["timestamp"] = datetime.utcnow().isoformat()
            
            # Color contrast testing
            if "color_contrast" in test_types or "all" in test_types:
                context = InvocationContext.create_new()
                color_issues = asyncio.run(
                    self.color_contrast_agent.analyze_accessibility(url, context)
                )
                test_results["issues"].extend(color_issues)
            
            # Keyboard focus testing  
            if "keyboard_focus" in test_types or "all" in test_types:
                context = InvocationContext.create_new()
                keyboard_issues = asyncio.run(
                    self.keyboard_focus_agent.analyze_accessibility(url, context)
                )
                test_results["issues"].extend(keyboard_issues)
            
            # Compile summary
            test_results["summary"] = self.compile_test_results(test_results["issues"])
            test_results["success"] = True
            
        except Exception as e:
            test_results["success"] = False
            test_results["error"] = str(e)
        
        return test_results
    
    @custom_function
    def compile_test_results(self, issues: List[AccessibilityIssue]) -> Dict[str, Any]:
        """
        Compile accessibility test results into summary
        
        Args:
            issues: List of accessibility issues found
            
        Returns:
            Compiled summary statistics
        """
        if not issues:
            return {
                "total_issues": 0,
                "by_severity": {},
                "by_agent": {},
                "compliance_score": 100
            }
        
        # Convert issues to dicts if needed
        issue_dicts = []
        for issue in issues:
            if hasattr(issue, '__dict__'):
                issue_dicts.append(issue.__dict__)
            else:
                issue_dicts.append(issue)
        
        # Count by severity
        by_severity = {}
        for issue in issue_dicts:
            severity = issue.get("severity", "unknown")
            if hasattr(severity, 'value'):
                severity = severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Count by agent
        by_agent = {}
        for issue in issue_dicts:
            agent = issue.get("agent_name", "unknown")
            by_agent[agent] = by_agent.get(agent, 0) + 1
        
        # Calculate compliance score (simplified)
        total_issues = len(issue_dicts)
        critical_count = by_severity.get("critical", 0)
        high_count = by_severity.get("high", 0)
        
        # Score calculation: 100 - weighted penalties
        score = 100 - (critical_count * 20) - (high_count * 10) - (total_issues * 2)
        compliance_score = max(0, min(100, score))
        
        return {
            "total_issues": total_issues,
            "by_severity": by_severity,
            "by_agent": by_agent,
            "compliance_score": compliance_score
        }
