# Server.py Explanation

## 🔗 Overview
`server.py` is a **local MCP server** using **stdio transport**. It's designed to be launched by MCP clients as a subprocess and communicates through stdin/stdout.

## 🏗️ Architecture
```
┌─────────────────┐    stdin/stdout   ┌─────────────────┐
│   MCP Client    │ ◄─────────────► │   MCP Server    │
│   (any client)  │   JSON-RPC over  │   (server.py)   │
└─────────────────┘   stdio pipes    └─────────────────┘
```

## 📋 Step-by-Step Breakdown

### 1. **Import FastMCP**
```python
from mcp.server.fastmcp import FastMCP
```
- **FastMCP**: Simplified MCP server implementation
- **Easy setup**: Minimal boilerplate code
- **Decorators**: Simple function decorators for tools/resources

### 2. **Create Server Instance**
```python
mcp = FastMCP("Hello Server")
```
- **Server name**: "Hello Server" (identifies this server)
- **Instance**: Creates FastMCP server object
- **Ready**: Server ready to register tools/resources

### 3. **Register Tool**
```python
@mcp.tool()
def greet(name: str = "world") -> str:
    """Return a personalised greeting"""
    return f"Hello, {name}!"
```
- **@mcp.tool()**: Decorator marks function as MCP tool
- **Parameters**: `name` with default value "world"
- **Return**: Simple string response
- **Docstring**: Used as tool description

### 4. **Register Resource**
```python
@mcp.resource("info://version")
def version() -> str:
    """Simple version string"""
    return "v0.0.1"
```
- **@mcp.resource()**: Decorator marks function as MCP resource
- **URI**: "info://version" - unique identifier for resource
- **Return**: String content of the resource
- **Static data**: Provides version information

### 5. **Register Prompt**
```python
@mcp.prompt(description="Prompt asking for a name to greet")
def ask_name() -> str:
    return "What name should I greet?"
```
- **@mcp.prompt()**: Decorator marks function as MCP prompt
- **Description**: Explains what the prompt does
- **Return**: The prompt text to display
- **Interactive**: Helps clients know what to ask

### 6. **Run Server**
```python
if __name__ == "__main__":
    mcp.run(transport="stdio")
```
- **stdio transport**: Communicate via stdin/stdout
- **Blocking**: Server runs until client disconnects
- **Process**: Designed to run as subprocess

## 🔄 Communication Flow

### Server Lifecycle:
1. **Start**: Client spawns server process
2. **Listen**: Server reads from stdin
3. **Process**: Handle JSON-RPC messages
4. **Respond**: Write responses to stdout
5. **Exit**: Terminate when client disconnects

### Message Handling:
```
stdin ──► JSON-RPC ──► Method Router ──► Tool/Resource/Prompt ──► Response ──► stdout
```

## 📨 Supported MCP Operations

### 1. **Tools** (AI-controlled functions)
```python
@mcp.tool()
def greet(name: str = "world") -> str:
    return f"Hello, {name}!"
```
- **Purpose**: Functions that AI can call
- **Parameters**: Type-annotated arguments
- **Return**: Results for AI consumption

### 2. **Resources** (App-controlled data)
```python
@mcp.resource("info://version")
def version() -> str:
    return "v0.0.1"
```
- **Purpose**: Static or dynamic data sources
- **URI**: Unique identifier for the resource
- **Return**: Content that can be read

### 3. **Prompts** (User interaction templates)
```python
@mcp.prompt(description="Prompt asking for a name to greet")
def ask_name() -> str:
    return "What name should I greet?"
```
- **Purpose**: Template prompts for user interaction
- **Description**: Explains prompt purpose
- **Return**: Text to show to user

## 🔧 JSON-RPC Message Examples

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
  "id": 1
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
  "id": 1
}
```

### Resource Read Request:
```json
{
  "jsonrpc": "2.0",
  "method": "resources/read",
  "params": {
    "uri": "info://version"
  },
  "id": 2
}
```

### Resource Read Response:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "contents": [
      {
        "uri": "info://version",
        "mimeType": "text/plain",
        "text": "v0.0.1"
      }
    ]
  },
  "id": 2
}
```

## ✅ Advantages of stdio Server

1. **Simple**: No network configuration
2. **Secure**: Local process communication
3. **Lightweight**: Minimal overhead
4. **Portable**: Works on any platform
5. **Debuggable**: Easy to test and debug

## ⚠️ Limitations

1. **Local only**: Cannot serve remote clients
2. **Single client**: One client at a time
3. **Process bound**: Dies when client disconnects
4. **No persistence**: No state between sessions

## 🎯 Use Cases

- **Development**: Local testing and development
- **Personal tools**: Individual productivity tools
- **Automation**: Script-based automation
- **Testing**: Unit tests for MCP functionality

## 🔧 Running the Server

### Direct execution (for testing):
```bash
python server.py
```
*Note: Server will wait for stdin input when run directly*

### Via client (normal usage):
```bash
python client.py
```
*Client automatically starts server.py as subprocess*

## 📋 FastMCP Features

- **Automatic registration**: Tools/resources auto-discovered
- **Type checking**: Parameter validation
- **Error handling**: Graceful error responses
- **Documentation**: Docstrings become descriptions
- **Minimal code**: Less boilerplate than raw MCP

This server demonstrates the simplest way to create an MCP server for local use!
