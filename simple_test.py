#!/usr/bin/env python3
"""
Simple test script to verify the AI Accessibility Testing Agent setup
"""

import sys
import os
import traceback

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import click
        print("✅ click imported successfully")
    except ImportError as e:
        print(f"❌ click import failed: {e}")
        return False
    
    try:
        import asyncio
        print("✅ asyncio imported successfully")
    except ImportError as e:
        print(f"❌ asyncio import failed: {e}")
        return False
    
    try:
        from mock_adk import LlmAgent, InvocationContext
        print("✅ mock ADK classes imported successfully")
    except ImportError as e:
        print(f"❌ mock ADK import failed: {e}")
        return False
    
    return True

def test_environment():
    """Test environment configuration"""
    print("\n🔧 Testing environment...")
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ .env file found")
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check API key
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            print(f"✅ ANTHROPIC_API_KEY configured (length: {len(api_key)})")
        else:
            print("❌ ANTHROPIC_API_KEY not found")
            return False
            
        # Check model
        model = os.getenv('CLAUDE_MODEL')
        if model:
            print(f"✅ CLAUDE_MODEL configured: {model}")
        else:
            print("❌ CLAUDE_MODEL not found")
            
    else:
        print("❌ .env file not found")
        return False
    
    return True

def test_simple_agent():
    """Test creating a simple agent"""
    print("\n🤖 Testing agent creation...")
    
    try:
        from mock_adk import LlmAgent
        
        # Create a simple test agent
        agent = LlmAgent(
            name="test_agent",
            description="A simple test agent",
            instruction="You are a helpful test agent",
            model="claude-3-5-sonnet-20241022"
        )
        
        print(f"✅ Test agent created: {agent.name}")
        print(f"   Model: {agent.model}")
        print(f"   Description: {agent.description}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        traceback.print_exc()
        return False

async def test_async_functionality():
    """Test async functionality"""
    print("\n⚡ Testing async functionality...")
    
    try:
        from mock_adk import LlmAgent
        
        agent = LlmAgent(name="async_test_agent")
        result = await agent.invoke("Hello, this is a test")
        
        print(f"✅ Async invoke successful: {result['response'][:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 AI Accessibility Testing Agent - Setup Verification")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Environment", test_environment),
        ("Agent Creation", test_simple_agent)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            if test_func():
                print(f"✅ {test_name} test PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            print(f"❌ {test_name} test ERROR: {e}")
    
    # Run async test
    print(f"\n📋 Running Async test...")
    try:
        import asyncio
        result = asyncio.run(test_async_functionality())
        if result:
            print("✅ Async test PASSED")
            passed += 1
        else:
            print("❌ Async test FAILED")
    except Exception as e:
        print(f"❌ Async test ERROR: {e}")
    
    total += 1  # Include async test
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for use.")
        print("\n🚀 Try running: python simple_test.py --demo")
        return True
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        return False

if __name__ == "__main__":
    if "--demo" in sys.argv:
        print("🎯 Running quick demo...")
        from mock_adk import LlmAgent
        agent = LlmAgent(name="demo_agent", description="Demo accessibility agent")
        print(f"Created demo agent: {agent.name}")
        print("✅ Demo completed successfully!")
    else:
        main()
