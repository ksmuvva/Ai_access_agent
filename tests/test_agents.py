"""
Test suite for the AI Accessibility Testing Agent
Tests the orchestrator and agents functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from orchestrator import AccessibilityOrchestrator
from agents.keyboard_focus_agent import KeyboardFocusAgent
from agents.color_contrast_agent import ColorContrastAgent
from agents.base_agent import AccessibilityIssue, TestSeverity

class TestAccessibilityOrchestrator:
    """Test the main orchestrator functionality"""
    
    @pytest.fixture
    def orchestrator(self):
        return AccessibilityOrchestrator()
    
    @pytest.fixture
    def sample_issues(self):
        return [
            AccessibilityIssue(
                agent_name="Test Agent",
                issue_type="TEST_ISSUE",
                severity=TestSeverity.HIGH,
                description="Test issue description",
                wcag_guideline="WCAG 2.2 - 1.1.1 Non-text Content"
            ),
            AccessibilityIssue(
                agent_name="Test Agent 2",
                issue_type="ANOTHER_TEST",
                severity=TestSeverity.MEDIUM,
                description="Another test issue",
                wcag_guideline="WCAG 2.2 - 1.4.3 Contrast (Minimum)"
            )
        ]
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test that orchestrator initializes correctly"""
        assert orchestrator.agent_registry is not None
        assert orchestrator.report_generator is not None
        assert orchestrator.test_results == {}
    
    @pytest.mark.asyncio
    async def test_run_accessibility_test(self, orchestrator, sample_issues):
        """Test running accessibility tests"""
        # Mock the agents
        with patch.object(orchestrator.agent_registry, 'get_all_agents') as mock_get_agents:
            mock_agent = AsyncMock()
            mock_agent.name = "Mock Agent"
            mock_agent.analyze = AsyncMock(return_value=sample_issues)
            mock_get_agents.return_value = [mock_agent]
            
            # Mock file operations
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('json.dump') as mock_json_dump:
                    await orchestrator.run_accessibility_test(
                        "https://example.com", 
                        ("all",), 
                        "test_report.json"
                    )
                    
                    # Verify agent was called
                    mock_agent.analyze.assert_called_once()
                    
                    # Verify report was saved
                    mock_file.assert_called_once()
                    mock_json_dump.assert_called_once()
    
    def test_issue_to_dict_conversion(self, orchestrator, sample_issues):
        """Test converting AccessibilityIssue to dictionary"""
        issue_dict = orchestrator._issue_to_dict(sample_issues[0])
        
        assert issue_dict['agent_name'] == "Test Agent"
        assert issue_dict['issue_type'] == "TEST_ISSUE"
        assert issue_dict['severity'] == "high"
        assert issue_dict['description'] == "Test issue description"
        assert issue_dict['wcag_guideline'] == "WCAG 2.2 - 1.1.1 Non-text Content"
    
    def test_priority_recommendation(self, orchestrator):
        """Test priority recommendation logic"""
        # Critical issues
        critical_counts = {
            TestSeverity.CRITICAL: 2,
            TestSeverity.HIGH: 0,
            TestSeverity.MEDIUM: 0,
            TestSeverity.LOW: 0,
            TestSeverity.INFO: 0
        }
        recommendation = orchestrator._get_priority_recommendation(critical_counts)
        assert "CRITICAL" in recommendation
        
        # High issues
        high_counts = {
            TestSeverity.CRITICAL: 0,
            TestSeverity.HIGH: 6,
            TestSeverity.MEDIUM: 0,
            TestSeverity.LOW: 0,
            TestSeverity.INFO: 0
        }
        recommendation = orchestrator._get_priority_recommendation(high_counts)
        assert "HIGH" in recommendation
        
        # Low issues only
        low_counts = {
            TestSeverity.CRITICAL: 0,
            TestSeverity.HIGH: 0,
            TestSeverity.MEDIUM: 2,
            TestSeverity.LOW: 3,
            TestSeverity.INFO: 1
        }
        recommendation = orchestrator._get_priority_recommendation(low_counts)
        assert "LOW" in recommendation

class TestKeyboardFocusAgent:
    """Test the keyboard focus agent"""
    
    @pytest.fixture
    def agent(self):
        return KeyboardFocusAgent()
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent.name == "Keyboard Focus Agent"
        assert "keyboard navigation" in agent.description.lower()
        assert agent.is_active is True
        assert len(agent.issues_found) == 0
    
    @pytest.mark.asyncio
    async def test_get_capabilities(self, agent):
        """Test agent capabilities"""
        capabilities = await agent.get_capabilities()
        
        assert capabilities['name'] == agent.name
        assert 'tests' in capabilities
        assert 'wcag_guidelines' in capabilities
        assert '2.1.1 Keyboard' in capabilities['wcag_guidelines']
        assert 'Tab Navigation' in capabilities['tests']
    
    @pytest.mark.asyncio
    async def test_validate_url_success(self, agent):
        """Test URL validation with successful response"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await agent.validate_url("https://example.com")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_url_failure(self, agent):
        """Test URL validation with failed response"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            result = await agent.validate_url("https://invalid-url.com")
            assert result is False
    
    def test_add_issue(self, agent):
        """Test adding issues to agent"""
        issue = AccessibilityIssue(
            agent_name=agent.name,
            issue_type="TEST_ISSUE",
            severity=TestSeverity.HIGH,
            description="Test issue"
        )
        
        agent.add_issue(issue)
        assert len(agent.issues_found) == 1
        assert agent.issues_found[0] == issue
    
    def test_get_issues_by_severity(self, agent):
        """Test filtering issues by severity"""
        high_issue = AccessibilityIssue(
            agent_name=agent.name,
            issue_type="HIGH_ISSUE",
            severity=TestSeverity.HIGH,
            description="High priority issue"
        )
        
        low_issue = AccessibilityIssue(
            agent_name=agent.name,
            issue_type="LOW_ISSUE", 
            severity=TestSeverity.LOW,
            description="Low priority issue"
        )
        
        agent.add_issue(high_issue)
        agent.add_issue(low_issue)
        
        high_issues = agent.get_issues_by_severity(TestSeverity.HIGH)
        assert len(high_issues) == 1
        assert high_issues[0] == high_issue
        
        low_issues = agent.get_issues_by_severity(TestSeverity.LOW)
        assert len(low_issues) == 1
        assert low_issues[0] == low_issue

class TestColorContrastAgent:
    """Test the color contrast agent"""
    
    @pytest.fixture
    def agent(self):
        return ColorContrastAgent()
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent.name == "Color Multi-Contrast Agent"
        assert "color contrast" in agent.description.lower()
        assert agent.contrast_requirements is not None
    
    def test_calculate_contrast_ratio(self, agent):
        """Test contrast ratio calculation"""
        # Black on white should have high contrast
        black = (0, 0, 0)
        white = (255, 255, 255)
        contrast = agent._calculate_contrast_ratio(black, white)
        assert contrast > 20  # Should be 21:1
        
        # Same colors should have 1:1 contrast
        same_contrast = agent._calculate_contrast_ratio(black, black)
        assert abs(same_contrast - 1.0) < 0.1
    
    def test_parse_rgb_color(self, agent):
        """Test RGB color parsing"""
        # RGB format
        rgb_color = agent._parse_rgb_color("rgb(255, 0, 0)")
        assert rgb_color == (255, 0, 0)
        
        # RGBA format
        rgba_color = agent._parse_rgb_color("rgba(0, 255, 0, 0.5)")
        assert rgba_color == (0, 255, 0)
        
        # Hex format
        hex_color = agent._parse_rgb_color("#0000FF")
        assert hex_color == (0, 0, 255)
        
        # Short hex format
        short_hex = agent._parse_rgb_color("#F0F")
        assert short_hex == (255, 0, 255)
    
    def test_is_large_text(self, agent):
        """Test large text detection"""
        # 18px is large text
        assert agent._is_large_text("18px") is True
        
        # 14px bold is large text
        assert agent._is_large_text("14px", "bold") is True
        
        # 12px normal is not large text
        assert agent._is_large_text("12px", "normal") is False
    
    @pytest.mark.asyncio
    async def test_get_capabilities(self, agent):
        """Test agent capabilities"""
        capabilities = await agent.get_capabilities()
        
        assert capabilities['name'] == agent.name
        assert 'tests' in capabilities
        assert 'wcag_guidelines' in capabilities
        assert '1.4.3 Contrast (Minimum)' in capabilities['wcag_guidelines']
        assert 'Text Contrast Ratios' in capabilities['tests']

def mock_open():
    """Mock file open for testing"""
    from unittest.mock import mock_open as original_mock_open
    return original_mock_open()

if __name__ == "__main__":
    pytest.main([__file__])
