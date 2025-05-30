# 🤖 AI Accessibility Testing Agent

A sophisticated multi-agent system for automated accessibility testing using Google's ADK Python framework. This tool helps ensure websites comply with WCAG 2.2 UK standards through intelligent AI-powered analysis.

## 🎯 Overview

The AI Accessibility Testing Agent is a modular, extensible system that orchestrates multiple specialized AI agents to perform comprehensive accessibility audits. Built specifically with Google's ADK Python framework, it provides automated testing capabilities for keyboard navigation, color contrast, and other accessibility requirements.

## 🏗️ Architecture

### Multi-Agent System
- **Orchestrator**: Coordinates all agents and manages test execution
- **Keyboard Focus Agent**: Tests keyboard navigation and focus management
- **Color Multi-Contrast Agent**: Analyzes color contrast ratios and visual accessibility
- **Base Agent Framework**: Extensible foundation for adding new agents

### Key Components
- **CLI Interface**: User-friendly command-line interface for test execution
- **Report Generator**: Comprehensive reporting in JSON and HTML formats
- **Natural Language Processing**: Accept natural language prompts for testing
- **WCAG 2.2 Compliance**: Built-in WCAG 2.2 UK standards compliance checking

## 🚀 Quick Start

### Installation

1. **Clone and install dependencies:**
```bash
git clone <repository-url>
cd ai-accessibility-agent
pip install -r requirements.txt
```

2. **Install Playwright browsers:**
```bash
playwright install
```

### Basic Usage

**Test a website with all agents:**
```bash
python main.py test https://example.com
```

**Test specific accessibility aspects:**
```bash
python main.py test https://example.com --agents keyboard-focus color-contrast
```

**Natural language testing:**
```bash
python main.py chat "check keyboard navigation for https://example.com"
```

**List available agents:**
```bash
python main.py list-agents
```

## 🤖 Available Agents

### 1. Keyboard Focus Agent
Tests keyboard navigation and focus management:
- Tab navigation completeness
- Focus indicator visibility
- Logical focus order
- Skip link functionality
- Keyboard trap detection
- Interactive element accessibility

**WCAG Guidelines Covered:**
- 2.1.1 Keyboard
- 2.1.2 No Keyboard Trap
- 2.4.1 Bypass Blocks
- 2.4.3 Focus Order
- 2.4.7 Focus Visible

### 2. Color Multi-Contrast Agent
Analyzes color contrast and visual accessibility:
- Text contrast ratio testing
- Link contrast verification
- Button/interactive element contrast
- Focus indicator contrast
- Color-only information detection
- Background image text analysis

**WCAG Guidelines Covered:**
- 1.4.1 Use of Color
- 1.4.3 Contrast (Minimum)
- 1.4.11 Non-text Contrast

## 📊 Report Generation

The system generates comprehensive reports in multiple formats:

### JSON Report Structure
```json
{
  "metadata": {
    "url": "https://example.com",
    "test_date": "2024-01-01T12:00:00",
    "wcag_version": "2.2",
    "compliance_level": "AA"
  },
  "summary": {
    "compliance_score": 85,
    "severity_breakdown": {...},
    "recommendation": "..."
  },
  "agent_results": {...},
  "issues_by_severity": {...},
  "detailed_issues": [...]
}
```

### HTML Report Features
- Visual compliance score
- Severity-based issue categorization
- Agent-specific results
- WCAG guideline mapping
- Actionable recommendations

## 🔧 Configuration

### Agent Configuration
Agents can be configured through their initialization parameters:

```python
# Example: Custom keyboard focus agent
agent = KeyboardFocusAgent()
agent.configure(
    test_depth='comprehensive',  # basic, standard, comprehensive
    timeout=30000,  # milliseconds
    custom_selectors=['[data-testid]']
)
```

### Orchestrator Settings
```python
orchestrator = AccessibilityOrchestrator()
orchestrator.configure(
    parallel_execution=True,
    max_concurrent_agents=3,
    timeout_per_agent=120000
)
```

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest -m unit

# Integration tests only  
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Test Coverage
```bash
pytest --cov=. --cov-report=html
```

## 🔄 Extending the System

### Adding New Agents

1. **Create agent class inheriting from BaseAccessibilityAgent:**
```python
from agents.base_agent import BaseAccessibilityAgent, AccessibilityIssue

class MyCustomAgent(BaseAccessibilityAgent):
    def __init__(self):
        super().__init__(
            name="My Custom Agent",
            description="Tests custom accessibility requirements"
        )
    
    async def analyze(self, url: str, context: Dict[str, Any]) -> List[AccessibilityIssue]:
        # Implement your testing logic
        pass
    
    async def get_capabilities(self) -> Dict[str, Any]:
        # Return agent capabilities
        pass
```

2. **Register the agent:**
```python
from agents import AgentRegistry

registry = AgentRegistry()
registry.register_agent('my-custom', MyCustomAgent)
```

### Custom Issue Types
```python
issue = AccessibilityIssue(
    agent_name="My Agent",
    issue_type="CUSTOM_ISSUE_TYPE",
    severity=TestSeverity.HIGH,
    description="Description of the issue",
    wcag_guideline="WCAG 2.2 - X.X.X Guideline Name",
    suggested_fix="How to fix this issue",
    evidence={"additional": "data"}
)
```

## 📋 CLI Reference

### Commands

**`test`** - Run accessibility tests
- `url`: Target URL to test (required)
- `--agents, -a`: Specific agents to run (default: all)
- `--output, -o`: Output file path (default: accessibility_report.json)
- `--verbose, -v`: Enable verbose logging

**`chat`** - Natural language interaction
- `prompt`: Natural language description of test requirements
- `--url`: Target URL (can also be extracted from prompt)

**`list-agents`** - Show available agents

### Examples
```bash
# Comprehensive test with custom output
python main.py test https://example.com -o detailed_report.json -v

# Keyboard-only testing
python main.py test https://example.com -a keyboard-focus

# Natural language testing
python main.py chat "check if this site https://example.com has good color contrast"
```

## 🎯 WCAG 2.2 UK Compliance

The system is specifically designed for WCAG 2.2 UK compliance testing:

### Supported Guidelines
- **Perceivable**: Color contrast, non-text content
- **Operable**: Keyboard accessibility, focus management
- **Understandable**: Clear navigation, consistent identification
- **Robust**: Compatible with assistive technologies

### Compliance Levels
- **Level A**: Basic accessibility features
- **Level AA**: Standard compliance (default target)
- **Level AAA**: Enhanced accessibility (optional)

## 🔒 Security Considerations

- All web requests use secure HTTPS when possible
- No sensitive data is stored in reports
- Browser automation runs in sandboxed environment
- User agents clearly identify as accessibility testing tools

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes with tests
4. Ensure all tests pass
5. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests before committing
pytest && flake8 && mypy .
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Check existing documentation
- Review WCAG 2.2 guidelines for accessibility requirements

## 🔄 Roadmap

### Upcoming Agents
- **Form Accessibility Agent**: Form labels, error handling, validation
- **Image Alt Text Agent**: Alternative text quality and appropriateness
- **Heading Structure Agent**: Proper heading hierarchy and navigation
- **ARIA Agent**: ARIA attributes and semantic markup
- **Mobile Accessibility Agent**: Touch targets and responsive design

### Enhanced Features
- Real-time monitoring and alerts
- CI/CD integration plugins
- Advanced natural language processing
- Machine learning-based issue prioritization
- Integration with popular testing frameworks
