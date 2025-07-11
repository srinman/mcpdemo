# How SSE Works in MCP (Model Context Protocol)

## 🔄 Overview

SSE (Server-Sent Events) is used by MCP to enable network communication between clients and servers. Here's how it works:

## 📡 Technical Details

### 1. **HTTP Connection**
```
Client → GET /sse HTTP/1.1
         Host: localhost:8000
         Accept: text/event-stream
         Cache-Control: no-cache

Server → HTTP/1.1 200 OK
         Content-Type: text/event-stream
         Cache-Control: no-cache
         Connection: keep-alive
```

### 2. **SSE Event Format**
```
data: {"jsonrpc": "2.0", "method": "tools/call", "params": {...}, "id": 1}

data: {"jsonrpc": "2.0", "result": {...}, "id": 1}

```

## 🖥️ Server Side (`servernetwork.py`)

### What FastMCP Does:
1. **HTTP Server**: Creates an HTTP server (using Uvicorn)
2. **SSE Endpoint**: Exposes `/sse` endpoint for SSE connections
3. **MCP Protocol**: Handles JSON-RPC messages over SSE
4. **Tool Execution**: Executes tools and returns results

### Server Flow:
```python
# 1. FastMCP starts HTTP server
mcp = FastMCP("Hello Server")

# 2. Registers tools, resources, prompts
@mcp.tool()
def greet(name: str = "world") -> str:
    return f"Hello Hello, {name}!"

# 3. Runs with SSE transport
mcp.run(transport="sse")  # Starts HTTP server on port 8000
```

### What happens internally:
1. **HTTP Server**: Uvicorn starts on `http://127.0.0.1:8000`
2. **SSE Route**: `/sse` endpoint accepts SSE connections
3. **Message Processing**: Incoming SSE messages are parsed as JSON-RPC
4. **Tool Dispatch**: Tools are called based on JSON-RPC method
5. **Response**: Results sent back as SSE events

## 💻 Client Side (`clientnetwork.py`)

### What the Client Does:
1. **HTTP GET**: Opens connection to `/sse` endpoint
2. **SSE Stream**: Receives SSE events from server
3. **Bidirectional**: Sends requests and receives responses
4. **JSON-RPC**: Uses JSON-RPC protocol over SSE

### Client Flow:
```python
# 1. Open SSE connection
async with sse_client(server_url) as (read, write):
    # 2. Create MCP session
    async with ClientSession(read, write) as session:
        # 3. Initialize protocol
        await session.initialize()
        # 4. Call tools
        result = await session.call_tool("greet", {"name": "Azure OpenAI"})
```

## 🔄 Message Flow Example

### 1. Client → Server (Initialize)
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {}
  },
  "id": 1
}
```

### 2. Server → Client (Initialize Response)
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {},
      "resources": {},
      "prompts": {}
    },
    "serverInfo": {
      "name": "Hello Server",
      "version": "1.0.0"
    }
  },
  "id": 1
}
```

### 3. Client → Server (Tool Call)
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "greet",
    "arguments": {
      "name": "Azure OpenAI"
    }
  },
  "id": 2
}
```

### 4. Server → Client (Tool Response)
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Hello Hello, Azure OpenAI!"
      }
    ]
  },
  "id": 2
}
```

## 🌐 Network Communication

### Local Network:
- **Server**: Binds to `127.0.0.1:8000` (localhost only)
- **Client**: Connects to `http://localhost:8000/sse`

### Remote Network:
- **Server**: Can bind to `0.0.0.0:8000` (all interfaces)
- **Client**: Connects to `http://SERVER_IP:8000/sse`

### Benefits of SSE:
1. **HTTP-based**: Works through firewalls and proxies
2. **Real-time**: Instant communication
3. **Reliable**: Built-in reconnection
4. **Simple**: Standard HTTP + event streaming

## 🔧 Why SSE for MCP?

1. **Firewall Friendly**: HTTP traffic is rarely blocked
2. **Proxy Compatible**: Works with HTTP proxies
3. **Bidirectional**: Can send requests both ways
4. **Efficient**: Single connection for multiple requests
5. **Standard**: Well-supported web technology

This makes MCP servers accessible over networks while maintaining the simplicity of HTTP-based communication!
