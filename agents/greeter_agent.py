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
