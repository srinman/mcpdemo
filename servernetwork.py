from mcp.server.fastmcp import FastMCP
import os

# Create the server
mcp = FastMCP("Hello Server")

# 1. TOOL — model-controlled
@mcp.tool()
def greet(name: str = "world") -> str:
    """Return a personalised greeting"""
    return f"Hello Hello, {name}!"

# 2. RESOURCE — app-controlled
@mcp.resource("info://version")
def version() -> str:
    """Simple version string"""
    return "v0.0.1"

# 3. PROMPT — user-controlled
@mcp.prompt(description="Prompt asking for a name to greet")
def ask_name() -> str:
    return "What name should I greet?"

if __name__ == "__main__":
    print("Starting MCP server with SSE transport")
    print("Server will be accessible at http://localhost:3000/sse")
    
    # Set environment variables for SSE transport
    os.environ["MCP_SSE_HOST"] = "0.0.0.0"
    os.environ["MCP_SSE_PORT"] = "3000"
    
    # Use SSE transport for network communication
    mcp.run(transport="sse")
