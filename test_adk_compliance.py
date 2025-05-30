#!/usr/bin/env python3
"""
Test script to check ADK compliance implementation
"""

import sys
import traceback

def test_imports():
    """Test if all new ADK agents can be imported"""
    try:
        print("Testing GreeterAgent import...")
        from agents.greeter_agent import GreeterAgent
        print("✅ GreeterAgent import successful")
        
        print("Testing TaskExecutionAgent import...")
        from agents.task_execution_agent import TaskExecutionAgent
        print("✅ TaskExecutionAgent import successful")
        
        print("Testing updated coordinator import...")
        from agents.adk_coordinator import AccessibilityCoordinatorAgent
        print("✅ AccessibilityCoordinatorAgent import successful")
        
        print("Testing orchestrator import...")
        from adk_orchestrator import ADKAccessibilityOrchestrator
        print("✅ ADKAccessibilityOrchestrator import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_agent_creation():
    """Test if agents can be created successfully"""
    try:
        print("\nTesting agent creation...")
        
        from agents.greeter_agent import GreeterAgent
        greeter = GreeterAgent()
        print("✅ GreeterAgent created successfully")
        
        from agents.task_execution_agent import TaskExecutionAgent
        task_executor = TaskExecutionAgent()
        print("✅ TaskExecutionAgent created successfully")
        
        print("✅ All agents created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        traceback.print_exc()
        return False

def test_adk_compliance():
    """Test ADK compliance features"""
    try:
        print("\nTesting ADK compliance...")
        
        from agents.greeter_agent import GreeterAgent
        greeter = GreeterAgent()
        
        # Test if it has the correct ADK attributes
        assert hasattr(greeter, 'name'), "Missing name attribute"
        assert hasattr(greeter, 'model'), "Missing model attribute"
        assert hasattr(greeter, 'description'), "Missing description attribute"
        print("✅ ADK agent attributes present")
        
        # Test custom functions
        capabilities = greeter.get_testing_capabilities()
        assert 'wcag_version' in capabilities, "Missing WCAG version in capabilities"
        assert capabilities['wcag_version'] == '2.2', "Incorrect WCAG version"
        print("✅ Custom functions working")
        
        print("✅ ADK compliance tests passed")
        return True
        
    except Exception as e:
        print(f"❌ ADK compliance test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🤖 ADK Compliance Test Suite")
    print("=" * 50)
    
    success = True
    
    # Run tests
    success &= test_imports()
    success &= test_agent_creation()
    success &= test_adk_compliance()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED - ADK Compliance Implementation Successful!")
        sys.exit(0)
    else:
        print("❌ TESTS FAILED - Implementation needs fixes")
        sys.exit(1)
