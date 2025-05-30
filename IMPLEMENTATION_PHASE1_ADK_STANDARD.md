# Google ADK Python & A2A Protocol Implementation Plan

## Implementation Status: Phase 1 - Standard ADK Agent Pattern

Based on the compliance analysis, I'll implement the required changes to achieve full ADK and A2A compliance. Starting with the most critical: implementing the standard ADK agent pattern with `greeter` + `task_executor` + `coordinator` structure.

## Priority 1: Standard ADK Agent Implementation

### Required Changes to Meet ADK Standards

1. **Create GreeterAgent following ADK patterns**
2. **Create TaskExecutionAgent following ADK patterns**  
3. **Update coordinator to use sub_agents=[greeter, task_executor] pattern**
4. **Integrate with existing accessibility testing capabilities**

## Implementation Details

### File: agents/greeter_agent.py (NEW)
```python
"""
Greeter Agent - Standard ADK Pattern
Handles user interaction and request routing for accessibility testing
"""

from typing import Dict, List, Any, Optional
from google.adk.agents import LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.tools import custom_function


class GreeterAgent(LlmAgent):
    """
    Standard ADK Greeter Agent for accessibility testing
    Handles initial user interaction and delegates to appropriate agents
    """
    
    def __init__(self):
        super().__init__(
            name="greeter",
            model="claude-3-5-sonnet-20241022",  # User requested Claude over Gemini
            description="Greeter agent for AI accessibility testing system",
            instruction="""
            You are a helpful accessibility testing greeter agent. Your role:
            
            1. Welcome users to the AI accessibility testing system
            2. Parse user requests for accessibility testing needs
            3. Identify the target URL and testing requirements
            4. Route requests to the appropriate task execution agent
            5. Provide guidance on WCAG 2.2 testing capabilities
            
            When users provide a URL or accessibility testing request:
            - Extract the target URL
            - Identify requested testing types (color contrast, keyboard nav, etc.)
            - Determine WCAG compliance level (A, AA, AAA)
            - Delegate to task_executor for actual testing
            
            Be friendly, helpful, and accessibility-focused.
            """,
            tools=[self._get_greeting_tools()]
        )
    
    def _get_greeting_tools(self) -> List:
        """Get tools available to the greeter agent"""
        return [
            self.parse_accessibility_request,
            self.get_testing_capabilities
        ]
    
    @custom_function
    def parse_accessibility_request(self, user_input: str) -> Dict[str, Any]:
        """
        Parse user input for accessibility testing requests
        
        Args:
            user_input: Raw user input containing URL and testing requirements
            
        Returns:
            Parsed request details for task execution
        """
        # Implementation for parsing user requests
        parsed_request = {
            "url": None,
            "test_types": [],
            "wcag_level": "AA",
            "priority": "medium"
        }
        
        # URL extraction logic
        import re
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, user_input)
        if urls:
            parsed_request["url"] = urls[0]
        
        # Test type detection
        if "color" in user_input.lower() or "contrast" in user_input.lower():
            parsed_request["test_types"].append("color_contrast")
        if "keyboard" in user_input.lower() or "navigation" in user_input.lower():
            parsed_request["test_types"].append("keyboard_focus")
        if not parsed_request["test_types"]:
            parsed_request["test_types"] = ["all"]
        
        # WCAG level detection
        if "aaa" in user_input.lower():
            parsed_request["wcag_level"] = "AAA"
        elif "level a" in user_input.lower() and "aa" not in user_input.lower():
            parsed_request["wcag_level"] = "A"
        
        return parsed_request
    
    @custom_function
    def get_testing_capabilities(self) -> Dict[str, Any]:
        """
        Get available accessibility testing capabilities
        
        Returns:
            Dictionary of available testing capabilities
        """
        return {
            "wcag_version": "2.2",
            "compliance_levels": ["A", "AA", "AAA"],
            "test_types": [
                "color_contrast",
                "keyboard_focus", 
                "screen_reader_compatibility",
                "aria_validation",
                "semantic_structure"
            ],
            "browsers_supported": ["chromium", "firefox", "webkit"],
            "output_formats": ["json", "html", "text"]
        }
    
    async def greet_and_delegate(self, user_input: str) -> Dict[str, Any]:
        """
        Main greeter method that handles user input and delegates to task executor
        
        Args:
            user_input: User's accessibility testing request
            
        Returns:
            Greeting response with next steps for task execution
        """
        # Parse the request
        parsed_request = self.parse_accessibility_request(user_input)
        
        # Create greeting response
        if parsed_request["url"]:
            greeting = f"Hello! I'll help you test {parsed_request['url']} for WCAG {parsed_request['wcag_level']} accessibility compliance."
            
            if parsed_request["test_types"] == ["all"]:
                greeting += " I'll run a comprehensive accessibility audit covering all our testing capabilities."
            else:
                test_types_str = ", ".join(parsed_request["test_types"])
                greeting += f" I'll focus on: {test_types_str}."
                
        else:
            greeting = "Hello! I'm your accessibility testing assistant. Please provide a URL to test for WCAG compliance."
            
        return {
            "greeting": greeting,
            "parsed_request": parsed_request,
            "next_action": "delegate_to_task_executor",
            "capabilities": self.get_testing_capabilities()
        }
```

### File: agents/task_execution_agent.py (NEW)
```python
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
```

### File: Updated agents/adk_coordinator.py

I need to update the coordinator to use the new standard ADK pattern:

```python
# Update the __init__ method to follow standard ADK pattern
def __init__(self):
    # Create standard ADK agents
    greeter = GreeterAgent()
    task_executor = TaskExecutionAgent()
    
    super().__init__(
        name="accessibility_coordinator",
        model="claude-3-5-sonnet-20241022",
        description="Master coordinator for accessibility testing using hierarchical sub-agents",
        instruction="""
        You are the main accessibility testing coordinator agent. Your responsibilities:
        
        1. COORDINATION: Manage sub-agents for comprehensive WCAG 2.2 testing
        2. WORKFLOW: Orchestrate greeter -> task_executor workflow
        3. A2A PROTOCOL: Communicate with remote accessibility agents when available
        4. AGGREGATION: Collect and synthesize findings from all agents
        5. REPORTING: Generate comprehensive accessibility reports
        
        Standard workflow:
        1. Greeter agent handles user interaction and request parsing
        2. Task executor performs actual accessibility testing
        3. Coordinator aggregates and reports results
        
        Always provide WCAG 2.2 guideline references and actionable fixes.
        """,
        sub_agents=[  # Standard ADK pattern - your requested example
            greeter,
            task_executor
        ]
    )
```

## Next Steps

1. **IMMEDIATE**: Create the new agent files
2. **Update**: Modify the coordinator to use the standard pattern
3. **Test**: Verify the new ADK-compliant structure works
4. **Integrate**: Ensure A2A protocol works with new structure

Would you like me to proceed with implementing these files?
