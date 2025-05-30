<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# AI Accessibility Testing Agent - Copilot Instructions

## Project Context
This is an AI-powered accessibility testing system built with Google's ADK Python framework. The system uses a multi-agent architecture to perform comprehensive WCAG 2.2 UK compliance testing.

## Framework Requirements
- **Strictly use Google ADK Python**: No CrewAI, LangChain, or other AI frameworks
- **Web automation**: Use Playwright for browser interactions
- **Testing**: Use pytest for all test implementations
- **Async programming**: All agents use async/await patterns

## Code Style Guidelines
- Follow PEP 8 Python style guidelines
- Use type hints for all function parameters and return types
- Implement comprehensive error handling with try/catch blocks
- Add detailed docstrings for all classes and methods
- Use descriptive variable names that indicate accessibility concepts

## Architecture Patterns
- All accessibility agents inherit from `BaseAccessibilityAgent`
- Use the `AccessibilityIssue` dataclass for consistent issue reporting
- Implement the `TestSeverity` enum for issue prioritization
- Follow the orchestrator pattern for agent coordination

## Accessibility Focus
- Map all issues to specific WCAG 2.2 guidelines
- Provide actionable recommendations for each issue found
- Use semantic HTML and ARIA concepts in code examples
- Consider keyboard navigation, screen readers, and visual impairments

## Testing Approach
- Write comprehensive unit tests for each agent
- Include integration tests for agent coordination
- Mock browser interactions for faster test execution
- Test edge cases and error conditions

## Comments and Documentation
- Explain accessibility concepts in comments
- Reference WCAG guidelines where applicable
- Include examples of both accessible and inaccessible patterns
- Document the reasoning behind contrast ratios and other calculations
