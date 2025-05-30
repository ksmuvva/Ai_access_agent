"""
Agent Card Implementation for A2A Protocol
Defines accessibility testing agent capabilities and service discovery
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json


@dataclass
class A2AMethod:
    """A2A protocol method definition"""
    name: str
    description: str
    params: Dict[str, Any]
    returns: Dict[str, Any]


@dataclass
class AccessibilityAgentCard:
    """
    Agent Card for A2A protocol service discovery
    Follows the A2A specification for agent registration and capabilities
    """
    # Required A2A fields
    name: str
    description: str
    version: str
    protocol_version: str = "1.0.0"
    
    # Accessibility-specific capabilities
    agent_type: str = "accessibility_tester"
    wcag_version: str = "2.2"
    compliance_levels: List[str] = None
    testing_capabilities: List[str] = None
    supported_browsers: List[str] = None
    
    # A2A service endpoints
    methods: List[A2AMethod] = None
    
    # Metadata
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        """Initialize default values"""
        if self.compliance_levels is None:
            self.compliance_levels = ["A", "AA", "AAA"]
            
        if self.testing_capabilities is None:
            self.testing_capabilities = [
                "color_contrast_analysis",
                "keyboard_navigation_testing", 
                "screen_reader_compatibility",
                "aria_validation",
                "semantic_structure_analysis",
                "focus_management_testing"
            ]
            
        if self.supported_browsers is None:
            self.supported_browsers = ["chromium", "firefox", "webkit"]
            
        if self.methods is None:
            self.methods = self._default_methods()
            
        if self.created_at is None:
            self.created_at = datetime.utcnow()
            
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def _default_methods(self) -> List[A2AMethod]:
        """Default A2A methods for accessibility testing agents"""
        return [
            A2AMethod(
                name="analyze_accessibility",
                description="Perform comprehensive WCAG 2.2 accessibility analysis",
                params={
                    "url": {"type": "string", "required": True, "description": "Target URL to analyze"},
                    "wcag_level": {"type": "string", "required": False, "default": "AA", "enum": ["A", "AA", "AAA"]},
                    "test_types": {"type": "array", "required": False, "items": {"type": "string"}}
                },
                returns={
                    "type": "object",
                    "properties": {
                        "issues": {"type": "array", "items": {"$ref": "#/definitions/AccessibilityIssue"}},
                        "summary": {"$ref": "#/definitions/TestSummary"},
                        "compliance_score": {"type": "number", "minimum": 0, "maximum": 100}
                    }
                }
            ),
            A2AMethod(
                name="test_color_contrast",
                description="Analyze color contrast compliance",
                params={
                    "url": {"type": "string", "required": True},
                    "wcag_level": {"type": "string", "required": False, "default": "AA"}
                },
                returns={
                    "type": "object",
                    "properties": {
                        "contrast_issues": {"type": "array"},
                        "compliant_elements": {"type": "number"}
                    }
                }
            ),
            A2AMethod(
                name="test_keyboard_navigation",
                description="Test keyboard accessibility and focus management",
                params={
                    "url": {"type": "string", "required": True},
                    "test_tab_order": {"type": "boolean", "required": False, "default": True}
                },
                returns={
                    "type": "object", 
                    "properties": {
                        "navigation_issues": {"type": "array"},
                        "focus_traps": {"type": "array"},
                        "tab_order_valid": {"type": "boolean"}
                    }
                }
            ),
            A2AMethod(
                name="validate_aria",
                description="Validate ARIA implementation and semantic markup",
                params={
                    "url": {"type": "string", "required": True}
                },
                returns={
                    "type": "object",
                    "properties": {
                        "aria_issues": {"type": "array"},
                        "semantic_score": {"type": "number"}
                    }
                }
            ),
            A2AMethod(
                name="get_capabilities",
                description="Get agent capabilities and supported features",
                params={},
                returns={
                    "type": "object",
                    "properties": {
                        "wcag_version": {"type": "string"},
                        "compliance_levels": {"type": "array"},
                        "testing_capabilities": {"type": "array"},
                        "supported_browsers": {"type": "array"}
                    }
                }
            )
        ]
    
    def to_json(self) -> str:
        """Convert agent card to JSON for A2A protocol"""
        data = asdict(self)
        
        # Convert datetime objects to ISO strings
        if isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()
        if isinstance(data['updated_at'], datetime):
            data['updated_at'] = data['updated_at'].isoformat()
            
        # Convert methods to dict format
        data['methods'] = [asdict(method) for method in self.methods]
        
        return json.dumps(data, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AccessibilityAgentCard':
        """Create agent card from JSON"""
        data = json.loads(json_str)
        
        # Convert ISO strings back to datetime objects
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
        # Convert methods back to A2AMethod objects
        if 'methods' in data:
            data['methods'] = [A2AMethod(**method) for method in data['methods']]
            
        return cls(**data)
    
    def validate(self) -> List[str]:
        """
        Validate agent card against A2A specification
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields validation
        if not self.name:
            errors.append("Agent name is required")
        if not self.description:
            errors.append("Agent description is required")
        if not self.version:
            errors.append("Agent version is required")
            
        # WCAG compliance validation
        valid_levels = ["A", "AA", "AAA"]
        if not all(level in valid_levels for level in self.compliance_levels):
            errors.append(f"Invalid compliance levels. Must be one of: {valid_levels}")
            
        # Methods validation
        if not self.methods:
            errors.append("At least one A2A method must be defined")
        else:
            for method in self.methods:
                if not method.name:
                    errors.append(f"Method name is required")
                if not method.description:
                    errors.append(f"Method description is required for {method.name}")
                    
        return errors


# Default agent cards for the accessibility testing system
COORDINATOR_AGENT_CARD = AccessibilityAgentCard(
    name="accessibility_coordinator",
    description="Master coordinator for comprehensive WCAG 2.2 accessibility testing using hierarchical sub-agents",
    version="1.0.0",
    testing_capabilities=[
        "comprehensive_accessibility_analysis",
        "multi_agent_coordination", 
        "wcag_compliance_reporting",
        "issue_prioritization",
        "remediation_recommendations"
    ]
)

COLOR_CONTRAST_AGENT_CARD = AccessibilityAgentCard(
    name="color_contrast_agent", 
    description="Specialized agent for color contrast and visual accessibility testing",
    version="1.0.0",
    testing_capabilities=[
        "color_contrast_analysis",
        "visual_accessibility_testing",
        "wcag_aa_aaa_compliance",
        "color_blindness_simulation"
    ]
)

KEYBOARD_FOCUS_AGENT_CARD = AccessibilityAgentCard(
    name="keyboard_focus_agent",
    description="Specialized agent for keyboard navigation and focus management testing", 
    version="1.0.0",
    testing_capabilities=[
        "keyboard_navigation_testing",
        "focus_management_validation", 
        "tab_order_analysis",
        "focus_trap_detection",
        "skip_link_validation"
    ]
)

GREETER_AGENT_CARD = AccessibilityAgentCard(
    name="accessibility_greeter",
    description="Entry point agent for accessibility testing workflow initiation",
    version="1.0.0", 
    testing_capabilities=[
        "user_interaction_management",
        "requirement_gathering",
        "workflow_initiation",
        "task_delegation"
    ]
)

TASK_EXECUTION_AGENT_CARD = AccessibilityAgentCard(
    name="accessibility_task_executor",
    description="Task execution coordinator for accessibility testing workflows",
    version="1.0.0",
    testing_capabilities=[
        "task_coordination",
        "workflow_management", 
        "result_aggregation",
        "error_handling",
        "report_generation"
    ]
)
