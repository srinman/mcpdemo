# Client.py Explanation

## 🔗 Overview
`client.py` demonstrates **local MCP communication** using **stdio transport**. This is the simplest way to use MCP where the client automatically starts and manages the server process.

## 🏗️ Architecture
```
┌─────────────────┐    subprocess    ┌─────────────────┐
│   MCP Client    │ ◄─────────────► │   MCP Server    │
│   (client.py)   │    stdin/stdout  │   (server.py)   │
└─────────────────┘                  └─────────────────┘
```

## 📋 Step-by-Step Breakdown

### 1. **Import Required Modules**
```python
import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
```
- `stdio_client`: Creates client that communicates via stdin/stdout
- `ClientSession`: Manages MCP protocol session
- `StdioServerParameters`: Configuration for server subprocess

### 2. **Configure Server Parameters**
```python
params = StdioServerParameters(command="python", args=["server.py"])
```
- **command**: `"python"` - Execute Python interpreter
- **args**: `["server.py"]` - Run server.py script
- **Result**: Client will run `python server.py` as subprocess

### 3. **Establish Connection**
```python
async with stdio_client(params) as (read, write):
```
- **Starts subprocess**: `python server.py`
- **Creates pipes**: stdin/stdout for communication
- **Returns streams**: `read` and `write` for I/O

### 4. **Create MCP Session**
```python
async with ClientSession(read, write) as session:
```
- **Protocol handling**: Manages MCP JSON-RPC protocol
- **Message routing**: Handles requests/responses
- **Error handling**: Manages connection errors

### 5. **Initialize Protocol**
```python
await session.initialize()
```
- **Handshake**: Exchange capabilities with server
- **Version check**: Ensure protocol compatibility
- **Setup**: Prepare for tool/resource calls

### 6. **Call Server Tool**
```python
result = await session.call_tool("greet", {"name": "Azure OpenAI"})
print(result.content[0].text)
```
- **Tool call**: Invoke `greet` tool on server
- **Parameters**: Pass `{"name": "Azure OpenAI"}`
- **Response**: Get result and print text content

## 🔄 Communication Flow

### Process Lifecycle:
1. **Start**: Client starts `python server.py` subprocess
2. **Connect**: Establishes stdin/stdout pipes
3. **Initialize**: MCP handshake
4. **Communicate**: Tool calls via JSON-RPC
5. **Cleanup**: Server process terminates when client exits

### Message Flow:
```
Client Process          Server Process
     │                       │
     │ 1. spawn subprocess    │
     │──────────────────────► │
     │                       │
     │ 2. MCP initialize      │
     │──────────────────────► │
     │                       │
     │ 3. capabilities        │
     │ ◄────────────────────── │
     │                       │
     │ 4. tool call request   │
     │──────────────────────► │
     │                       │
     │ 5. tool call response  │
     │ ◄────────────────────── │
     │                       │
     │ 6. cleanup/terminate   │
     │──────────────────────► │
```

## 📨 JSON-RPC Messages

### Initialize Request:
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

### Tool Call Request:
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

### Tool Call Response:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Hello, Azure OpenAI!"
      }
    ]
  },
  "id": 2
}
```

## ✅ Advantages of stdio Transport

1. **Simple**: No network configuration needed
2. **Secure**: Local process communication only
3. **Automatic**: Server lifecycle managed by client
4. **Reliable**: Direct process communication
5. **Development**: Perfect for testing and development

## ⚠️ Limitations

1. **Local only**: Cannot connect to remote servers
2. **Single client**: One client per server process
3. **Process overhead**: Spawns new process each time
4. **No persistence**: Server dies when client disconnects

## 🎯 Use Cases

- **Development**: Testing MCP tools locally
- **Automation**: Scripts that need MCP functionality
- **Single-user**: Personal tools and utilities
- **Testing**: Unit tests for MCP servers

## 🔧 Running the Client

```bash
# Make sure server.py exists in the same directory
python client.py
```

**Output:**
```
Hello, Azure OpenAI!
```

This demonstrates the simplest form of MCP communication where everything runs locally on your machine!
