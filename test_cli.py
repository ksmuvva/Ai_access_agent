#!/usr/bin/env python3
"""
Simple CLI Test Script for AI Accessibility Testing Agent
Tests the system components without running the full CLI
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_imports():
    """Test if all imports work correctly"""
    print("🔍 Testing imports...")
    
    try:
        # Test basic imports
        import click
        print("✅ Click imported")
        
        from utils.logger import setup_logger
        print("✅ Logger imported")
        
        from utils.report_generator import ReportGenerator
        print("✅ Report generator imported")
        
        # Test agent imports with fallback
        try:
            from agents.adk_coordinator import AccessibilityCoordinatorAgent
            print("✅ ADK coordinator imported")
        except ImportError as e:
            print(f"⚠️  ADK coordinator import failed: {e}")
            
        try:
            from adk_orchestrator import ADKAccessibilityOrchestrator
            print("✅ ADK orchestrator imported")
        except ImportError as e:
            print(f"⚠️  ADK orchestrator import failed: {e}")
            
        print("✅ Import test completed")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

async def test_environment():
    """Test environment configuration"""
    print("\n🌍 Testing environment...")
    
    try:
        # Check for .env file
        env_file = project_root / ".env"
        if env_file.exists():
            print("✅ .env file found")
        else:
            print("⚠️  .env file not found")
            
        # Test environment loading
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key and api_key.startswith('sk-ant-'):
            print("✅ Anthropic API key configured")
        else:
            print("⚠️  Anthropic API key not properly configured")
            
        print("✅ Environment test completed")
        return True
        
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

async def test_basic_functionality():
    """Test basic system functionality"""
    print("\n⚙️ Testing basic functionality...")
    
    try:
        # Test logger setup
        logger = setup_logger("test")
        logger.info("Test log message")
        print("✅ Logger working")
        
        # Test report generator
        report_gen = ReportGenerator()
        test_data = {
            "total_issues": 0,
            "issues_by_severity": {"critical": 0, "major": 0, "minor": 0},
            "test_metadata": {"timestamp": "2024-01-01T00:00:00Z"}
        }
        report = report_gen.generate_summary_report(test_data)
        print("✅ Report generator working")
        
        print("✅ Basic functionality test completed")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

async def test_cli_commands():
    """Test CLI command availability"""
    print("\n🖥️ Testing CLI commands...")
    
    try:
        # Import main CLI
        import main
        
        # Check if CLI groups exist
        if hasattr(main, 'cli'):
            print("✅ Main CLI group found")
            
            # Check for expected commands
            commands = main.cli.commands
            expected_commands = ['test', 'chat', 'list-agents']
            
            for cmd in expected_commands:
                if cmd in commands:
                    print(f"✅ Command '{cmd}' available")
                else:
                    print(f"⚠️  Command '{cmd}' not found")
                    
        print("✅ CLI commands test completed")
        return True
        
    except Exception as e:
        print(f"❌ CLI commands test failed: {e}")
        return False

async def run_all_tests():
    """Run all system tests"""
    print("🚀 Starting AI Accessibility Testing Agent System Check")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Environment Test", test_environment),
        ("Basic Functionality Test", test_basic_functionality),
        ("CLI Commands Test", test_cli_commands)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System ready for accessibility testing.")
        return True
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
