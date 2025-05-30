"""
Integration tests for the AI Accessibility Testing Agent
Tests the full system functionality end-to-end
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from main import cli
from click.testing import CliRunner

class TestCLIIntegration:
    """Test the CLI interface"""
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    def test_cli_version(self, runner):
        """Test CLI version command"""
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
    
    def test_list_agents_command(self, runner):
        """Test list agents command"""
        result = runner.invoke(cli, ['list-agents'])
        assert result.exit_code == 0
        assert "keyboard-focus" in result.output
        assert "color-contrast" in result.output
    
    @patch('orchestrator.AccessibilityOrchestrator.run_accessibility_test')
    def test_test_command(self, mock_run_test, runner):
        """Test the main test command"""
        mock_run_test.return_value = asyncio.Future()
        mock_run_test.return_value.set_result(None)
        
        result = runner.invoke(cli, [
            'test', 
            'https://example.com',
            '--agents', 'keyboard-focus',
            '--output', 'test_report.json'
        ])
        
        # Note: This might fail due to asyncio in CLI, but tests the structure
        mock_run_test.assert_called_once()
    
    @patch('orchestrator.AccessibilityOrchestrator.process_natural_language_prompt')
    def test_chat_command(self, mock_process_prompt, runner):
        """Test the chat command"""
        mock_process_prompt.return_value = asyncio.Future()
        mock_process_prompt.return_value.set_result(None)
        
        result = runner.invoke(cli, [
            'chat',
            'check accessibility for https://example.com'
        ])
        
        mock_process_prompt.assert_called_once()

class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_accessibility_test_workflow(self):
        """Test a complete accessibility testing workflow"""
        from orchestrator import AccessibilityOrchestrator
        
        orchestrator = AccessibilityOrchestrator()
        
        # Mock the agents to avoid actual web scraping
        with patch.object(orchestrator.agent_registry, 'get_all_agents') as mock_get_agents:
            # Create mock agents with sample results
            mock_keyboard_agent = Mock()
            mock_keyboard_agent.name = "Keyboard Focus Agent"
            mock_keyboard_agent.analyze = AsyncMock(return_value=[
                MockAccessibilityIssue(
                    agent_name="Keyboard Focus Agent",
                    issue_type="NO_SKIP_LINKS",
                    severity="medium",
                    description="No skip links found"
                )
            ])
            
            mock_color_agent = Mock()
            mock_color_agent.name = "Color Multi-Contrast Agent"
            mock_color_agent.analyze = AsyncMock(return_value=[
                MockAccessibilityIssue(
                    agent_name="Color Multi-Contrast Agent",
                    issue_type="LOW_TEXT_CONTRAST",
                    severity="high",
                    description="Text contrast too low"
                )
            ])
            
            mock_get_agents.return_value = [mock_keyboard_agent, mock_color_agent]
            
            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            try:
                # Run the test
                await orchestrator.run_accessibility_test(
                    "https://example.com",
                    ("all",),
                    temp_filename
                )
                
                # Verify output file was created and contains expected data
                assert os.path.exists(temp_filename)
                
                with open(temp_filename, 'r') as f:
                    report_data = json.load(f)
                
                # Verify report structure
                assert 'metadata' in report_data
                assert 'summary' in report_data
                assert 'agent_results' in report_data
                assert 'detailed_issues' in report_data
                
                # Verify metadata
                assert report_data['metadata']['url'] == "https://example.com"
                assert report_data['metadata']['wcag_version'] == "2.2"
                
                # Verify issues were found
                assert len(report_data['detailed_issues']) == 2
                
                # Verify agent results
                assert "Keyboard Focus Agent" in report_data['agent_results']
                assert "Color Multi-Contrast Agent" in report_data['agent_results']
                
            finally:
                # Clean up
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)
    
    @pytest.mark.asyncio
    async def test_natural_language_processing(self):
        """Test natural language prompt processing"""
        from orchestrator import AccessibilityOrchestrator
        
        orchestrator = AccessibilityOrchestrator()
        
        # Mock the run_accessibility_test method
        with patch.object(orchestrator, 'run_accessibility_test') as mock_run_test:
            mock_run_test.return_value = None
            
            # Test keyboard-focused prompt
            await orchestrator.process_natural_language_prompt(
                "check keyboard navigation for https://example.com",
                None
            )
            
            # Verify correct agents were selected
            call_args = mock_run_test.call_args
            agents_called = call_args[0][1]  # Second argument is agents tuple
            assert 'keyboard-focus' in agents_called
    
    def test_report_generation(self):
        """Test report generation functionality"""
        from utils.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        # Sample report data
        sample_report = {
            'metadata': {
                'url': 'https://example.com',
                'test_date': '2024-01-01T12:00:00',
                'wcag_version': '2.2',
                'compliance_level': 'AA'
            },
            'summary': {
                'compliance_score': 75,
                'severity_breakdown': {
                    'critical': 0,
                    'high': 2,
                    'medium': 3,
                    'low': 1,
                    'info': 0
                },
                'recommendation': 'HIGH: Multiple high-priority issues need attention'
            },
            'agent_results': {
                'Keyboard Focus Agent': {
                    'issues_found': 3,
                    'severity_breakdown': {'critical': 0, 'high': 1, 'medium': 2, 'low': 0, 'info': 0}
                }
            },
            'issues_by_severity': {
                'high': [
                    {
                        'agent_name': 'Test Agent',
                        'issue_type': 'TEST_ISSUE',
                        'severity': 'high',
                        'description': 'Test description',
                        'wcag_guideline': 'WCAG 2.2 - 1.1.1',
                        'suggested_fix': 'Test fix'
                    }
                ]
            },
            'issues_by_wcag_guideline': {},
            'detailed_issues': []
        }
        
        # Generate HTML report
        html_report = generator.generate_html_report(sample_report)
        
        # Verify HTML structure
        assert '<!DOCTYPE html>' in html_report
        assert 'AI Accessibility Test Report' in html_report
        assert 'https://example.com' in html_report
        assert 'Compliance Score: 75/100' in html_report
        assert 'HIGH: Multiple high-priority issues need attention' in html_report

class MockAccessibilityIssue:
    """Mock accessibility issue for testing"""
    
    def __init__(self, agent_name, issue_type, severity, description, wcag_guideline=None):
        self.agent_name = agent_name
        self.issue_type = issue_type
        self.severity = MockSeverity(severity)
        self.description = description
        self.wcag_guideline = wcag_guideline
        self.element_selector = None
        self.suggested_fix = None
        self.evidence = None

class MockSeverity:
    """Mock severity enum for testing"""
    
    def __init__(self, value):
        self.value = value

if __name__ == "__main__":
    pytest.main([__file__])
