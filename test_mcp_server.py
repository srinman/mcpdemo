#!/usr/bin/env python3
"""
Test client for the enhanced MCP server
This tests all the tools without needing Azure OpenAI credentials
"""

import asyncio
from mcp.client.sse import sse_client
from mcp import ClientSession

async def test_mcp_tools():
    """Test all MCP tools"""
    print("🧪 Testing Enhanced MCP Server Tools")
    print("=" * 40)
    
    server_url = "http://localhost:8000/sse"
    
    try:
        async with sse_client(server_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test 1: Greet tool
                print("\n🔧 Testing greet tool:")
                result = await session.call_tool("greet", {"name": "MCP Tester"})
                print(f"   Result: {result.content[0].text}")
                
                # Test 2: Calculate tool
                print("\n🔧 Testing calculate tool:")
                result = await session.call_tool("calculate", {
                    "operation": "multiply",
                    "a": 12,
                    "b": 8
                })
                print(f"   Result: {result.content[0].text}")
                
                # Test 3: System info tool
                print("\n🔧 Testing get_system_info tool:")
                result = await session.call_tool("get_system_info", {})
                print(f"   Result: {result.content[0].text[:100]}...")
                
                # Test 4: Save file tool
                print("\n🔧 Testing save_text_file tool:")
                result = await session.call_tool("save_text_file", {
                    "filename": "test_mcp.txt",
                    "content": "Hello from MCP test!"
                })
                print(f"   Result: {result.content[0].text}")
                
                # Test 5: Read file tool
                print("\n🔧 Testing read_text_file tool:")
                result = await session.call_tool("read_text_file", {
                    "filename": "test_mcp.txt"
                })
                print(f"   Result: {result.content[0].text}")
                
                # Test 6: Weather tool
                print("\n🔧 Testing get_weather tool:")
                result = await session.call_tool("get_weather", {
                    "city": "Seattle"
                })
                print(f"   Result: {result.content[0].text}")
                
                # Test 7: List available tools
                print("\n📋 Available tools:")
                tools = await session.list_tools()
                for tool in tools.tools:
                    print(f"   • {tool.name}: {tool.description}")
                
                # Test 8: List available resources
                print("\n📚 Available resources:")
                resources = await session.list_resources()
                for resource in resources.resources:
                    print(f"   • {resource.name}: {resource.description}")
                
                print("\n✅ All tests completed successfully!")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the MCP server is running: python azure_mcp_server.py")

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
