import asyncio
from mcp.client.sse import sse_client
from mcp import ClientSession

async def main():
    # === SSE CONNECTION ESTABLISHMENT ===
    # 1. Client opens HTTP connection to server's SSE endpoint
    # 2. Server responds with SSE headers: Content-Type: text/event-stream
    # 3. Connection stays open for bidirectional JSON-RPC over SSE
    server_url = "http://localhost:8000/sse"  # Change to your server's URL
    
    print("🔗 Establishing SSE connection to server...")
    async with sse_client(server_url) as (read, write):
        print("✅ SSE connection established!")
        
        # === MCP SESSION INITIALIZATION ===
        # Creates MCP session over the SSE transport
        async with ClientSession(read, write) as session:
            print("🤝 Initializing MCP session...")
            await session.initialize()
            print("✅ MCP session initialized!")
            
            # === MCP TOOL CALL ===
            # Send JSON-RPC request over SSE to call server's 'greet' tool
            print("🔧 Calling 'greet' tool with parameter...")
            result = await session.call_tool("greet", {"name": "Azure OpenAI"})
            print(f"📨 Received response: {result.content[0].text}")

asyncio.run(main())
