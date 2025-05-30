"""
LLM Service for AI Accessibility Testing Agent
Integrates Claude 3.5 Sonnet for natural language processing and tool calling
"""

import os
import json
from typing import Dict, List, Optional, Any
from anthropic import Anthropic
from dotenv import load_dotenv
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger(__name__)

class LLMService:
    """Service for interacting with Claude 3.5 Sonnet for accessibility testing"""
    
    def __init__(self):
        """Initialize the LLM service with Claude configuration"""
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')
        self.max_tokens = int(os.getenv('MAX_TOKENS', '4000'))
        self.temperature = float(os.getenv('TEMPERATURE', '0.1'))
        
        logger.info(f"LLM Service initialized with model: {self.model}")
    
    def analyze_accessibility_prompt(self, prompt: str, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a natural language prompt to determine accessibility testing strategy
        
        Args:
            prompt: User's natural language request
            url: Optional target URL
            
        Returns:
            Dictionary with analysis results and testing recommendations
        """
        system_prompt = """You are an AI accessibility testing expert specializing in WCAG 2.2 compliance.
        
        Your role is to analyze user prompts and recommend appropriate accessibility testing strategies.
        
        Available testing agents:
        1. keyboard-focus: Tests keyboard navigation, focus management, tab order, skip links
        2. color-contrast: Tests color contrast ratios, visual accessibility, color-only information
        
        For each user prompt, determine:
        1. Which agents to run (keyboard-focus, color-contrast, or both)
        2. Specific tests to prioritize based on the request
        3. Expected issues to look for
        4. User-friendly explanation of what will be tested
        
        Respond in JSON format with:
        {
            "agents_to_run": ["keyboard-focus", "color-contrast"],
            "test_focus": "description of what to test",
            "expected_issues": ["list of potential issues"],
            "user_explanation": "user-friendly explanation"
        }"""
        
        user_message = f"User prompt: {prompt}"
        if url:
            user_message += f"\nTarget URL: {url}"
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            
            # Parse the JSON response
            response_text = response.content[0].text
            return json.loads(response_text)
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            # Fallback response
            return {
                "agents_to_run": ["keyboard-focus", "color-contrast"],
                "test_focus": "general accessibility testing",
                "expected_issues": ["various accessibility issues"],
                "user_explanation": "Running comprehensive accessibility tests"
            }
    
    def generate_accessibility_insights(self, test_results: Dict[str, Any], user_prompt: str) -> str:
        """
        Generate human-readable insights from accessibility test results
        
        Args:
            test_results: Results from accessibility testing
            user_prompt: Original user request
            
        Returns:
            Human-readable analysis and recommendations
        """
        system_prompt = """You are an accessibility expert providing insights on test results.
        
        Analyze the accessibility test results and provide:
        1. Summary of findings in plain language
        2. Prioritized recommendations for fixes
        3. WCAG 2.2 compliance assessment
        4. Next steps for improvement
        
        Be specific, actionable, and user-friendly in your response."""
        
        user_message = f"""
        Original user request: {user_prompt}
        
        Test results:
        {json.dumps(test_results, indent=2)}
        
        Please provide insights and recommendations.
        """
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return "Unable to generate detailed insights at this time. Please review the test results manually."
    
    def suggest_accessibility_improvements(self, issues: List[Dict[str, Any]]) -> List[str]:
        """
        Generate specific improvement suggestions based on identified issues
        
        Args:
            issues: List of accessibility issues found
            
        Returns:
            List of actionable improvement suggestions
        """
        if not issues:
            return ["No accessibility issues found! Your site appears to be well-optimized."]
        
        system_prompt = """You are an accessibility consultant providing specific, actionable improvement suggestions.
        
        For each accessibility issue, provide:
        1. Clear explanation of the problem
        2. Step-by-step fix instructions
        3. Code examples when applicable
        4. WCAG guideline reference
        
        Be practical and specific in your recommendations."""
        
        issues_text = json.dumps(issues, indent=2)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": f"Accessibility issues to fix:\n{issues_text}"}]
            )
            
            # Split response into individual suggestions
            suggestions = response.content[0].text.split('\n\n')
            return [s.strip() for s in suggestions if s.strip()]
            
        except Exception as e:
            logger.error(f"Suggestion generation failed: {e}")
            return ["Please review the accessibility issues and refer to WCAG 2.2 guidelines for fixes."]

# Global LLM service instance
llm_service = None

def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance"""
    global llm_service
    if llm_service is None:
        llm_service = LLMService()
    return llm_service
