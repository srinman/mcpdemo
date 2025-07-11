#!/usr/bin/env python3
"""
Comprehensive test script for the basic MCP server (server.py)
This tests all functionality without needing network connections
"""

import asyncio
import sys
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

async def test_basic_server():
    """Comprehensive test of server.py"""
    print("🧪 Testing Basic MCP Server (server.py)")
    print("=" * 40)
    
    params = StdioServerParameters(command="python", args=["server.py"])
    
    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test 1: Greet tool
                print("✅ Testing greet tool:")
                result = await session.call_tool("greet", {"name": "Tester"})
                print(f"   Result: {result.content[0].text}")
                
                # Test 2: Greet tool with default parameter
                print("✅ Testing greet tool (default parameter):")
                result = await session.call_tool("greet", {})
                print(f"   Result: {result.content[0].text}")
                
                # Test 3: Version resource
                print("✅ Testing version resource:")
                result = await session.read_resource("info://version")
                print(f"   Version: {result.contents[0].text}")
                
                # Test 4: List tools
                print("✅ Available tools:")
                tools = await session.list_tools()
                for tool in tools.tools:
                    print(f"   • {tool.name}: {tool.description}")
                
                # Test 5: List resources
                print("✅ Available resources:")
                resources = await session.list_resources()
                for resource in resources.resources:
                    print(f"   • {resource.name}: {resource.description}")
                
                # Test 6: List prompts
                print("✅ Available prompts:")
                prompts = await session.list_prompts()
                for prompt in prompts.prompts:
                    print(f"   • {prompt.name}: {prompt.description}")
                
                # Test 7: Get prompt
                print("✅ Testing prompt:")
                result = await session.get_prompt("ask_name", {})
                print(f"   Prompt: {result.messages[0].content.text}")
                
                print("\n🎉 All tests passed!")
                print("📊 Summary:")
                print(f"   • {len(tools.tools)} tools available")
                print(f"   • {len(resources.resources)} resources available")
                print(f"   • {len(prompts.prompts)} prompts available")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("💡 Make sure server.py exists and is syntactically correct")
        return False
    
    return True

async def test_error_handling():
    """Test error handling scenarios"""
    print("\n🧪 Testing Error Handling")
    print("=" * 25)
    
    params = StdioServerParameters(command="python", args=["server.py"])
    
    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test 1: Non-existent tool
                print("✅ Testing non-existent tool:")
                try:
                    result = await session.call_tool("nonexistent_tool", {})
                    print(f"   Unexpected success: {result}")
                except Exception as e:
                    print(f"   Expected error: {type(e).__name__}")
                
                # Test 2: Non-existent resource
                print("✅ Testing non-existent resource:")
                try:
                    result = await session.read_resource("info://nonexistent")
                    print(f"   Unexpected success: {result}")
                except Exception as e:
                    print(f"   Expected error: {type(e).__name__}")
                
                print("\n✅ Error handling tests completed!")
                
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False
    
    return True

async def performance_test():
    """Test performance with multiple calls"""
    print("\n🧪 Performance Test")
    print("=" * 18)
    
    params = StdioServerParameters(command="python", args=["server.py"])
    
    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                import time
                start_time = time.time()
                
                # Make multiple calls
                for i in range(10):
                    result = await session.call_tool("greet", {"name": f"User{i}"})
                    # Don't print all results, just verify they work
                
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"✅ 10 tool calls completed in {duration:.2f} seconds")
                print(f"   Average: {duration/10:.3f} seconds per call")
                
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False
    
    return True

async def main():
    """Run all tests"""
    print("🚀 MCP Basic Server Test Suite")
    print("=" * 30)
    
    # Run basic functionality tests
    success1 = await test_basic_server()
    
    # Run error handling tests
    success2 = await test_error_handling()
    
    # Run performance tests
    success3 = await performance_test()
    
    # Summary
    print("\n📊 Test Summary:")
    print(f"   Basic functionality: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Error handling: {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"   Performance: {'✅ PASS' if success3 else '❌ FAIL'}")
    
    if all([success1, success2, success3]):
        print("\n🎉 All tests passed! Your server.py is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
