"""
Test configuration for the AI Accessibility Testing Agent test suite
"""

import pytest
import asyncio
import sys
import os

# Add the project root to the Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure pytest for async testing
@pytest.fixture(scope='session')
def event_loop():
    """Create an instance of the default event loop for the test session."""
    if sys.platform.startswith('win'):
        # Use ProactorEventLoop on Windows for better compatibility
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Test configuration
pytest_plugins = []

# Configure test markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

# Test collection configuration
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Mark integration tests
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Mark unit tests
        if "test_agents" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Mark slow tests (those that might use web scraping or browser automation)
        if any(keyword in item.name.lower() for keyword in ['browser', 'scraping', 'playwright']):
            item.add_marker(pytest.mark.slow)
