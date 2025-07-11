# ServerNetwork.py Explanation

## 🔗 Overview
`servernetwork.py` is a **network-accessible MCP server** using **SSE (Server-Sent Events) transport**. It creates an HTTP server that clients can connect to from anywhere on the network.

## 🏗️ Architecture
```
┌─────────────────┐    HTTP/SSE      ┌─────────────────┐
│   MCP Client    │ ◄─────────────► │   MCP Server    │
│ (any machine)   │   port 8000      │ (servernetwork) │
└─────────────────┘                  └─────────────────┘
         │                                     │
         │            Network                  │
         │ ◄─────────────────────────────────► │
    Other clients                        HTTP Server
                                        (Uvicorn/FastAPI)
```

## 📋 Step-by-Step Breakdown

### 1. **Import Required Modules**
```python
from mcp.server.fastmcp import FastMCP
import os
```
- **FastMCP**: Simplified MCP server with SSE support
- **os**: For environment variable configuration

### 2. **Create Server Instance**
```python
mcp = FastMCP("Hello Server")
```
- **Server name**: "Hello Server" (network identifier)
- **Instance**: FastMCP server with network capabilities
- **Ready**: Server ready for network tools/resources

### 3. **Register Network Tool**
```python
@mcp.tool()
def greet(name: str = "world") -> str:
    """Return a personalised greeting"""
    return f"Hello Hello, {name}!"
```
- **@mcp.tool()**: Network-accessible tool
- **Parameters**: Same as local version
- **Return**: String response sent over network
- **Network**: Available to any connected client

### 4. **Register Network Resource**
```python
@mcp.resource("info://version")
def version() -> str:
    """Simple version string"""
    return "v0.0.1"
```
- **@mcp.resource()**: Network-accessible resource
- **URI**: "info://version" - global identifier
- **Return**: Version info accessible over network
- **Shared**: Available to all connected clients

### 5. **Register Network Prompt**
```python
@mcp.prompt(description="Prompt asking for a name to greet")
def ask_name() -> str:
    return "What name should I greet?"
```
- **@mcp.prompt()**: Network-accessible prompt
- **Description**: Explains prompt purpose
- **Return**: Prompt text for any client
- **Global**: Available to all connected clients

### 6. **Configure Network Settings**
```python
# Set environment variables for SSE transport
os.environ["MCP_SSE_HOST"] = "0.0.0.0"
os.environ["MCP_SSE_PORT"] = "3000"
```
- **Host**: "0.0.0.0" accepts connections from any IP
- **Port**: "3000" (though FastMCP uses 8000 by default)
- **Network**: Makes server accessible on local network

### 7. **Run Network Server**
```python
mcp.run(transport="sse")
```
- **SSE transport**: HTTP-based Server-Sent Events
- **HTTP server**: Creates Uvicorn server on port 8000
- **Persistent**: Runs until manually stopped
- **Multi-client**: Can handle multiple simultaneous clients

## 🔄 Network Communication Flow

### Server Startup:
1. **HTTP Server**: FastMCP starts Uvicorn on port 8000
2. **SSE Endpoint**: Creates `/sse` endpoint for connections
3. **Listen**: Waits for client connections
4. **Ready**: Server accessible at `http://localhost:8000/sse`

### Client Connection:
```
Client                    Network                    Server
  │                         │                         │
  │ 1. HTTP GET /sse        │                         │
  │────────────────────────►│────────────────────────►│
  │                         │                         │
  │ 2. SSE Headers          │                         │
  │◄────────────────────────│◄────────────────────────│
  │                         │                         │
  │ 3. MCP Initialize       │                         │
  │────────────────────────►│────────────────────────►│
  │                         │                         │
  │ 4. Capabilities         │                         │
  │◄────────────────────────│◄────────────────────────│
  │                         │                         │
  │ 5. Tool Calls           │                         │
  │◄───────────────────────►│◄───────────────────────►│
```

## 📨 HTTP/SSE Protocol Details

### SSE Connection Headers:
```http
GET /sse HTTP/1.1
Host: localhost:8000
Accept: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

### SSE Response Headers:
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
Access-Control-Allow-Origin: *
```

### SSE Event Format:
```
data: {"jsonrpc": "2.0", "method": "tools/call", "params": {...}, "id": 1}

data: {"jsonrpc": "2.0", "result": {...}, "id": 1}

```

## 🌐 Network Capabilities

### Local Network Access:
```python
# Server accessible on local network
server_url = "http://192.168.1.100:8000/sse"
```

### Multiple Clients:
```python
# Client 1
await session.call_tool("greet", {"name": "Client 1"})

# Client 2 (simultaneously)
await session.call_tool("greet", {"name": "Client 2"})
```

### Cross-Platform:
- **Windows**: Can connect to Linux server
- **macOS**: Can connect to Windows server
- **Linux**: Can connect to any server
- **Mobile**: Can connect via HTTP

## 🔧 Server Console Output

```
Starting MCP server with SSE transport
Server will be accessible at http://localhost:3000/sse
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

## 📡 Network Configuration

### Firewall Configuration:
```bash
# Allow incoming connections on port 8000
sudo ufw allow 8000/tcp
```

### Find Server IP:
```bash
# Get server's IP address
ip addr show | grep "inet " | grep -v 127.0.0.1
```

### Client Connection:
```python
# Connect from remote machine
server_url = "http://SERVER_IP:8000/sse"
```

## ✅ Advantages of Network Server

1. **Remote access**: Clients can connect from anywhere
2. **Multi-client**: Multiple simultaneous connections
3. **Persistent**: Server runs continuously
4. **Scalable**: Can handle many clients
5. **Cross-platform**: Works across different OS
6. **Firewall-friendly**: Uses standard HTTP port

## ⚠️ Network Considerations

1. **Security**: No authentication by default
2. **Firewall**: Port 8000 must be accessible
3. **Performance**: Network latency affects response time
4. **Resources**: Server must handle multiple clients
5. **Monitoring**: Need to monitor server health

## 🎯 Use Cases

- **Team collaboration**: Shared MCP server for team
- **Remote work**: Access tools from anywhere
- **Microservices**: MCP server as a service
- **Development**: Shared development tools
- **Production**: Scalable MCP services

## 🔧 Running the Network Server

### Start server:
```bash
python servernetwork.py
```

### Connect from client:
```bash
# Update clientnetwork.py with server URL
python clientnetwork.py
```

### Remote connection:
```python
# In clientnetwork.py
server_url = "http://YOUR_SERVER_IP:8000/sse"
```

## 📋 FastMCP Network Features

- **Automatic HTTP server**: Uvicorn server included
- **SSE transport**: Built-in Server-Sent Events
- **Multiple clients**: Concurrent client support
- **Error handling**: Network error recovery
- **Logging**: Built-in request logging

This server demonstrates how to make MCP tools available over the network for remote access and collaboration!
