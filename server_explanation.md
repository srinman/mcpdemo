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

## 🔧 Testing the Server

There are **multiple ways** to test the `server.py` MCP server:

### **Method 1: Using the Dedicated Client (Recommended)**
```bash
python client.py
```
- **How it works**: `client.py` spawns `server.py` as subprocess
- **Communication**: stdio transport (stdin/stdout)
- **Output**: "Hello Hello, Azure OpenAI!" (tests the greet tool)
- **Advantage**: Tests the intended usage pattern

### **Method 2: Manual Testing with MCP Client**
```python
import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

async def test_server():
    params = StdioServerParameters(command="python", args=["server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Test greet tool
            result = await session.call_tool("greet", {"name": "Test User"})
            print(f"Greet result: {result.content[0].text}")
            
            # Test resource
            result = await session.read_resource("info://version")
            print(f"Version: {result.contents[0].text}")
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")

asyncio.run(test_server())
```

### **Method 3: Direct Execution (Limited)**
```bash
python server.py
```
- **Behavior**: Server starts and waits for JSON-RPC input on stdin
- **Manual testing**: Type JSON-RPC messages manually
- **Example input**:
```json
{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "greet", "arguments": {"name": "Test"}}, "id": 1}
```
- **Not recommended**: Difficult to format JSON correctly

### **Method 4: Integration Testing**
Use the comprehensive test script (works with network servers):
```bash
# First start a network server (like azure_mcp_server.py)
python azure_mcp_server.py

# Then run the test script
python test_mcp_server.py
```

### **Method 6: Interactive Testing with MCP Inspector (Proxy Server)**

The **MCP Inspector** is a powerful debugging tool that creates a proxy server for interactive testing:

#### **Installation**:
```bash
npm install -g @modelcontextprotocol/inspector
```

#### **Usage**:
```bash
mcp-inspector python server.py
```

#### **What it does**:
- **Proxy server**: Creates a web-based interface to your MCP server
- **Interactive**: Click buttons to test tools, resources, and prompts
- **Real-time**: See JSON-RPC messages in real-time
- **Debugging**: Inspect all communication between client and server

#### **Features**:
- 🌐 **Web UI**: Opens in your browser (usually http://localhost:5173)
- 🔧 **Tool Testing**: Click to call tools with custom parameters
- 📚 **Resource Browser**: Browse and read all resources
- 💬 **Prompt Tester**: Test prompt templates
- 🔍 **Message Inspector**: See raw JSON-RPC messages
- 📊 **Server Stats**: Monitor server performance

#### **Example Session**:
```bash
$ mcp-inspector python server.py
MCP Inspector starting...
Server: python server.py
Web interface: http://localhost:5173
```

Then in your browser:
1. Navigate to `http://localhost:5173`
2. See your server's tools, resources, and prompts
3. Click "Call Tool" to test the `greet` function
4. Enter parameters: `{"name": "Inspector User"}`
5. See the result: `"Hello Hello, Inspector User!"`
6. View the raw JSON-RPC communication

#### **Advantages**:
- **Visual interface**: No need to write test code
- **Real-time feedback**: Immediate results
- **Protocol inspection**: See actual JSON-RPC messages
- **Parameter testing**: Easy to test different inputs
- **No coding required**: Perfect for non-developers

#### **Example Inspector UI**:
```
┌─────────────────────────────────────────────────────────────┐
│ MCP Inspector - Hello Server                                │
├─────────────────────────────────────────────────────────────┤
│ Tools:                                                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ greet                                                   │ │
│ │ Description: Return a personalised greeting             │ │
│ │ Parameters: {"name": "world"}                           │ │
│ │ [Call Tool]                                             │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Resources:                                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ info://version                                          │ │
│ │ Description: Simple version string                      │ │
│ │ [Read Resource]                                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Prompts:                                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ask_name                                                │ │
│ │ Description: Prompt asking for a name to greet         │ │
│ │ [Get Prompt]                                            │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### **Method 7: Using MCP CLI Tool**

Another interactive option is the MCP CLI tool:

#### **Installation**:
```bash
npm install -g @modelcontextprotocol/cli
```

#### **Usage**:
```bash
mcp-cli python server.py
```

#### **Interactive Commands**:
```bash
# List available tools
> list-tools

# Call a tool
> call-tool greet {"name": "CLI User"}

# Read a resource
> read-resource info://version

# List resources
> list-resources

# Get a prompt
> get-prompt ask_name {}

# Help
> help
```

#### **Example Session**:
```bash
$ mcp-cli python server.py
Connected to MCP server: Hello Server
Type 'help' for available commands.

> list-tools
Available tools:
- greet: Return a personalised greeting

> call-tool greet {"name": "CLI Tester"}
Result: Hello Hello, CLI Tester!

> read-resource info://version
Resource content: v0.0.1

> exit
```

### **Testing Methods Summary**

| Method | Best For | Advantages | Requirements |
|--------|----------|------------|--------------|
| **client.py** | Quick verification | Simple, built-in | Python only |
| **Manual MCP Client** | Custom testing | Full control | Python coding |
| **Direct Execution** | JSON-RPC debugging | Low-level access | Manual JSON formatting |
| **Integration Testing** | Network servers | Comprehensive | Network server running |
| **Interactive Testing** | Development | Full API coverage | Python coding |
| **MCP Inspector** | **🌟 Visual debugging** | **Web UI, no coding** | **Node.js/npm** |
| **MCP CLI** | **🌟 Command-line testing** | **Interactive shell** | **Node.js/npm** |
| **Automated Testing** | CI/CD | Repeatable | Python script |

#### **🎯 Recommended Testing Flow**:
1. **Start with**: `python client.py` (quick verification)
2. **Debug with**: `mcp-inspector python server.py` (visual testing)
3. **Explore with**: `mcp-cli python server.py` (interactive commands)
4. **Automate with**: `python test_basic_server.py` (comprehensive testing)

### **Expected Test Results**

#### **Greet Tool Test**:
```
Input: {"name": "Test User"}
Output: "Hello Hello, Test User!"
```

#### **Version Resource Test**:
```
URI: "info://version"
Output: "v0.0.1"
```

#### **Tool Discovery Test**:
```
Available tools: ["greet"]
Tool description: "Return a personalised greeting"
```

#### **Resource Discovery Test**:
```
Available resources: ["info://version"]
Resource description: "Simple version string"
```

#### **Prompt Discovery Test**:
```
Available prompts: ["ask_name"]
Prompt description: "Prompt asking for a name to greet"
```

### **Troubleshooting Testing**

#### **Common Issues**:
1. **"Server not responding"**: Check if server.py has syntax errors
2. **"Connection refused"**: Make sure you're using stdio transport, not network
3. **"Tool not found"**: Verify tool registration with `@mcp.tool()` decorator
4. **"Import errors"**: Ensure `mcp` package is installed (`pip install mcp`)
5. **"mcp-inspector not found"**: Install with `npm install -g @modelcontextprotocol/inspector`
6. **"Port already in use"**: Kill existing inspector processes or use different port
7. **"Browser not opening"**: Manually navigate to http://localhost:5173

#### **Inspector-Specific Troubleshooting**:
```bash
# Check if inspector is installed
npm list -g @modelcontextprotocol/inspector

# Install if missing
npm install -g @modelcontextprotocol/inspector

# Run with custom port
mcp-inspector --port 3000 python server.py

# Run with verbose logging
mcp-inspector --verbose python server.py
```

#### **CLI-Specific Troubleshooting**:
```bash
# Check if CLI is installed
npm list -g @modelcontextprotocol/cli

# Install if missing
npm install -g @modelcontextprotocol/cli

# Get help
mcp-cli --help
```

#### **Debug Mode**:
```python
# Add debug output to server.py
if __name__ == "__main__":
    print("Starting server...", file=sys.stderr)  # Goes to stderr, not stdout
    mcp.run(transport="stdio")
```

### **Automated Testing Script**

Create a `test_basic_server.py` file:
```python
#!/usr/bin/env python3
import asyncio
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
                
                # Test 2: Version resource
                print("✅ Testing version resource:")
                result = await session.read_resource("info://version")
                print(f"   Version: {result.contents[0].text}")
                
                # Test 3: List capabilities
                print("✅ Server capabilities:")
                tools = await session.list_tools()
                resources = await session.list_resources()
                prompts = await session.list_prompts()
                
                print(f"   Tools: {len(tools.tools)}")
                print(f"   Resources: {len(resources.resources)}")
                print(f"   Prompts: {len(prompts.prompts)}")
                
                print("\n🎉 All tests passed!")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_basic_server())
```

Run with:
```bash
python test_basic_server.py
```

## � Quick Testing Reference

### **One-Line Testing Commands**:
```bash
# 1. Quick verification
python client.py

# 2. Visual debugging (recommended)
mcp-inspector python server.py

# 3. Interactive command-line
mcp-cli python server.py

# 4. Comprehensive testing
python test_basic_server.py
```

### **Prerequisites**:
```bash
# Python dependencies
pip install mcp

# Node.js dependencies (for visual tools)
npm install -g @modelcontextprotocol/inspector
npm install -g @modelcontextprotocol/cli
```

### **Expected Outputs**:
- **client.py**: `"Hello Hello, Azure OpenAI!"`
- **mcp-inspector**: Web UI at http://localhost:5173
- **mcp-cli**: Interactive shell with MCP commands
- **test_basic_server.py**: Comprehensive test results

## �📋 FastMCP Features

- **Automatic registration**: Tools/resources auto-discovered
- **Type checking**: Parameter validation
- **Error handling**: Graceful error responses
- **Documentation**: Docstrings become descriptions
- **Minimal code**: Less boilerplate than raw MCP

This server demonstrates the simplest way to create an MCP server for local use!
