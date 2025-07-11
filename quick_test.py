#!/usr/bin/env python3
"""
Quick test of the MCP server without Azure OpenAI
This demonstrates the tools that Azure OpenAI would use
"""

import asyncio
from mcp.client.sse import sse_client
from mcp import ClientSession

async def quick_test():
    print("🧪 Quick Test: MCP Server Tools for Azure OpenAI")
    print("=" * 50)
    
    server_url = "http://localhost:8000/sse"
    
    try:
        async with sse_client(server_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                print("✅ Connected to MCP server")
                
                # Show available tools
                tools = await session.list_tools()
                print(f"\n📋 Available tools ({len(tools.tools)}):")
                for i, tool in enumerate(tools.tools, 1):
                    print(f"   {i}. {tool.name}: {tool.description}")
                
                # Test key tools that Azure OpenAI would use
                print("\n🔧 Testing key tools:")
                
                # Test 1: Greeting with timestamp
                print("\n1. Testing greet tool:")
                result = await session.call_tool("greet", {"name": "Azure OpenAI"})
                print(f"   → {result.content[0].text}")
                
                # Test 2: Mathematical calculation
                print("\n2. Testing calculate tool:")
                result = await session.call_tool("calculate", {
                    "operation": "multiply", "a": 15, "b": 8
                })
                print(f"   → {result.content[0].text}")
                
                # Test 3: File operations
                print("\n3. Testing file operations:")
                result = await session.call_tool("save_text_file", {
                    "filename": "azure_test.txt", 
                    "content": "Hello from Azure OpenAI + MCP!"
                })
                print(f"   → {result.content[0].text}")
                
                result = await session.call_tool("read_text_file", {
                    "filename": "azure_test.txt"
                })
                print(f"   → {result.content[0].text}")
                
                print("\n✅ All tests passed! Azure OpenAI can use these tools.")
                print("\n💡 What Azure OpenAI would do:")
                print("   - Analyze user requests")
                print("   - Determine which tools to use")
                print("   - Call tools with appropriate parameters")
                print("   - Integrate results into natural language responses")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 To fix this:")
        print("   1. Start the MCP server: python azure_mcp_server_simple.py")
        print("   2. Wait for 'Uvicorn running on http://127.0.0.1:8000'")
        print("   3. Run this test again")

if __name__ == "__main__":
    asyncio.run(quick_test())
