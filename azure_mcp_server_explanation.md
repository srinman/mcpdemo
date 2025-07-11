# Azure ## 🏗️ Server Architecture

```
┌─────────────────┐    HTTP/SSE      ┌─────────────────┐    Tools/APIs    ┌─────────────────┐
│   Azure Client  │ ◄─────────────► │   MCP Server    │ ◄─────────────► │  Local System   │
│ (Python App)    │   port 8000      │ (azure_mcp_    │   Direct calls   │ (Files, Math,   │
│                 │                  │  server.py)     │                  │  System Info)   │
└─────────────────┘                  └─────────────────┘                  └─────────────────┘
         │                                     │                                     │
         │            Network                  │              Local                  │
         │ ◄─────────────────────────────────► │ ◄─────────────────────────────────► │
    Remote clients                      HTTP Server                        OS/Files
                                        (Uvicorn/FastAPI)                   (Direct access)
```

## � Network Protocol Details

### SSE Connection Headers:
```http
GET /sse HTTP/1.1
Host: localhost:8000
Accept: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
User-Agent: mcp-client/1.0
```

### SSE Response Headers:
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
```

### MCP Tool Call (JSON-RPC over SSE):
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "calculate",
    "arguments": {
      "operation": "multiply",
      "a": 15,
      "b": 8
    }
  },
  "id": 1
}
```

### MCP Tool Response:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Result: 15.0 multiply 8.0 = 120.0"
      }
    ]
  },
  "id": 1
}
```

## �🔄 Server Communication Flow

### Server Startup Sequence:
1. **Environment Setup**: Load configuration and dependencies
2. **Tool Registration**: Register 6 tool categories (greet, calculate, etc.)
3. **Resource Registration**: Register info resources and examples
4. **HTTP Server**: Start Uvicorn on 0.0.0.0:8000
5. **SSE Endpoint**: Create `/sse` endpoint for MCP connections
6. **Ready**: Server accessible for client connections

### Client Connection Flow:
```
Client                    Network                    Server                    Tools
  │                         │                         │                         │
  │ 1. HTTP GET /sse        │                         │                         │
  │────────────────────────►│────────────────────────►│                         │
  │                         │                         │                         │
  │ 2. SSE Stream Opens     │                         │                         │
  │◄────────────────────────│◄────────────────────────│                         │
  │                         │                         │                         │
  │ 3. MCP Initialize       │                         │                         │
  │────────────────────────►│────────────────────────►│                         │
  │                         │                         │                         │
  │ 4. List Tools Request   │                         │                         │
  │────────────────────────►│────────────────────────►│                         │
  │                         │                         │                         │
  │ 5. Tool Definitions     │                         │                         │
  │◄────────────────────────│◄────────────────────────│                         │
  │                         │                         │                         │
  │ 6. Tool Call Request    │                         │                         │
  │────────────────────────►│────────────────────────►│                         │
  │                         │                         │                         │
  │                         │                         │ 7. Execute Tool         │
  │                         │                         │────────────────────────►│
  │                         │                         │                         │
  │                         │                         │ 8. Tool Result          │
  │                         │                         │◄────────────────────────│
  │                         │                         │                         │
  │ 9. Tool Response        │                         │                         │
  │◄────────────────────────│◄────────────────────────│                         │
```

### Multi-Tool Execution Flow:
```
Client Request: "Calculate 15 * 8 and save to file"

Client                    Server                    System
  │                         │                         │
  │ 1. calculate(15, 8)     │                         │
  │────────────────────────►│                         │
  │                         │ 2. Math operation       │
  │                         │────────────────────────►│
  │                         │ 3. Result: 120          │
  │                         │◄────────────────────────│
  │ 4. Result: 120          │                         │
  │◄────────────────────────│                         │
  │                         │                         │
  │ 5. save_file(calc.txt)  │                         │
  │────────────────────────►│                         │
  │                         │ 6. Write to file        │
  │                         │────────────────────────►│
  │                         │ 7. File saved           │
  │                         │◄────────────────────────│
  │ 8. File saved           │                         │
  │◄────────────────────────│                         │
```rver Code Explanation

This document provides a detailed explanation of `azure_mcp_server.py` - the enhanced MCP server that provides tools for Azure OpenAI integration.

## 🎯 What This Server Does

The `azure_mcp_server.py` file creates a **comprehensive MCP server** that provides multiple tools for Azure OpenAI to use. It's designed to demonstrate the full capabilities of MCP in a production-ready scenario.

## 🏗️ Server Architecture

```
Network Clients ←→ SSE (HTTP) ←→ MCP Server ←→ Local System/Files
     (Port 8000)                  (FastMCP)     (Tools & Resources)
```

## 📋 Code Structure Breakdown

### 1. **Server Initialization**

```python
from mcp.server.fastmcp import FastMCP
import os
import json
import datetime

# Create the server with enhanced capabilities
mcp = FastMCP("Azure OpenAI MCP Server")
```

**Purpose**: 
- Uses FastMCP for rapid server development
- Creates a named server instance
- Imports required modules for various tools

### 2. **Tool Categories**

The server provides **6 distinct tool categories**:

#### **A. Greeting Tool - Real-time Interaction**

```python
@mcp.tool()
def greet(name: str = "world") -> str:
    """Return a personalized greeting with current timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"Hello {name}! Current time: {timestamp}"
```

**Purpose**: 
- Demonstrates real-time capabilities
- Shows personalization with parameters
- Provides timestamp for context

**Azure OpenAI Usage**: 
- "Hello! Can you greet me?"
- "What time is it?"
- "Say hello to John"

#### **B. Calculation Tool - Mathematical Operations**

```python
@mcp.tool()
def calculate(operation: str, a: float, b: float) -> str:
    """Perform mathematical operations (add, subtract, multiply, divide)"""
    try:
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                return "Error: Division by zero"
            result = a / b
        else:
            return f"Error: Unknown operation '{operation}'. Use: add, subtract, multiply, divide"
        
        return f"Result: {a} {operation} {b} = {result}"
    except Exception as e:
        return f"Error: {str(e)}"
```

**Purpose**: 
- Provides mathematical capabilities
- Handles multiple operations
- Includes error handling (division by zero)
- Demonstrates parameter validation

**Azure OpenAI Usage**: 
- "Calculate 15 * 8"
- "What's 100 divided by 4?"
- "Add 25 and 17"

#### **C. System Information Tool - System Access**

```python
@mcp.tool()
def get_system_info() -> str:
    """Get basic system information"""
    import platform
    
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }
    
    # Try to add psutil info if available
    try:
        import psutil
        info["cpu_count"] = psutil.cpu_count()
        info["memory_gb"] = round(psutil.virtual_memory().total / (1024**3), 2)
    except ImportError:
        info["note"] = "psutil not available - install with: pip install psutil"
    
    return json.dumps(info, indent=2)
```

**Purpose**: 
- Provides system information access
- Demonstrates optional dependencies (psutil)
- Shows JSON formatting
- Handles missing dependencies gracefully

**Azure OpenAI Usage**: 
- "What system am I running on?"
- "Tell me about this computer"
- "How much memory does this machine have?"

#### **D. File Operations - File System Access**

```python
@mcp.tool()
def save_text_file(filename: str, content: str) -> str:
    """Save text content to a file"""
    try:
        with open(filename, 'w') as f:
            f.write(content)
        return f"Successfully saved content to {filename}"
    except Exception as e:
        return f"Error saving file: {str(e)}"

@mcp.tool()
def read_text_file(filename: str) -> str:
    """Read text content from a file"""
    try:
        with open(filename, 'r') as f:
            content = f.read()
        return f"Content of {filename}:\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"
```

**Purpose**: 
- Provides file system operations
- Demonstrates persistent storage
- Shows error handling for file operations
- Enables data persistence between conversations

**Azure OpenAI Usage**: 
- "Save this message to a file called notes.txt"
- "Read the contents of config.txt"
- "Write a summary to summary.txt"

#### **E. Weather Mock Tool - API Simulation**

```python
@mcp.tool()
def get_weather(city: str = "Seattle") -> str:
    """Get mock weather information for a city"""
    # This is a mock implementation - in real scenarios, you'd call a weather API
    import random
    
    weather_conditions = ["sunny", "cloudy", "rainy", "partly cloudy", "snowy"]
    temperature = random.randint(15, 85)  # Fahrenheit
    condition = random.choice(weather_conditions)
    
    return f"Weather in {city}: {temperature}°F, {condition}"
```

**Purpose**: 
- Simulates external API calls
- Shows how to integrate with external services
- Demonstrates randomized responses
- Template for real API integrations

**Azure OpenAI Usage**: 
- "What's the weather like in San Francisco?"
- "Check the weather in New York"
- "Is it raining in Seattle?"

### 3. **Resources - Information Access**

```python
@mcp.resource("info://server-capabilities")
def server_capabilities() -> str:
    """Information about this MCP server's capabilities"""
    return """
    This MCP server provides the following capabilities:
    - Personalized greetings with timestamps
    - Mathematical calculations (add, subtract, multiply, divide)
    - System information retrieval
    - File operations (read/write text files)
    - Mock weather information
    
    This server is designed to be used by Azure OpenAI to enhance its capabilities
    with real-time data and system operations.
    """

@mcp.resource("info://usage-examples")
def usage_examples() -> str:
    """Examples of how to use this MCP server"""
    return """
    Example tool calls:
    1. greet(name="Azure OpenAI") - Get personalized greeting
    2. calculate(operation="add", a=10, b=5) - Perform math operations
    3. get_system_info() - Get system information
    4. save_text_file(filename="test.txt", content="Hello World") - Save file
    5. read_text_file(filename="test.txt") - Read file
    6. get_weather(city="San Francisco") - Get weather info
    """
```

**Purpose**: 
- Provides self-documenting capabilities
- Shows server introspection
- Helps AI understand available tools
- Provides usage examples

### 4. **Prompts - User Interaction Templates**

```python
@mcp.prompt(description="Ask user what they want to calculate")
def calculation_prompt() -> str:
    return "What mathematical operation would you like me to perform? Please provide the operation (add, subtract, multiply, divide) and two numbers."

@mcp.prompt(description="Ask user for file operations")
def file_operations_prompt() -> str:
    return "What file operation would you like me to perform? I can save text to files or read existing text files."
```

**Purpose**: 
- Provides conversation starters
- Helps guide user interactions
- Shows available functionality
- Enables proactive assistance

### 5. **Server Configuration & Launch**

```python
if __name__ == "__main__":
    print("🚀 Starting Enhanced MCP Server for Azure OpenAI")
    print("📡 Server will be accessible at http://localhost:8000/sse")
    print("🔧 Available tools: greet, calculate, get_system_info, save_text_file, read_text_file, get_weather")
    print("📚 Available resources: server-capabilities, usage-examples")
    print("💡 Available prompts: calculation_prompt, file_operations_prompt")
    print()
    
    # Set environment variables for network access
    os.environ["MCP_SSE_HOST"] = "0.0.0.0"
    os.environ["MCP_SSE_PORT"] = "8000"
    
    # Run with SSE transport for network access
    mcp.run(transport="sse")
```

**Purpose**: 
- Configures network accessibility
- Sets up SSE transport on port 8000
- Provides startup information
- Binds to all network interfaces (0.0.0.0)

## 🌐 Network Flow & Architecture

### **Detailed Network Flow**

```
1. Server Startup:
   ┌─────────────────────────────────────────────────────────────────┐
   │ python azure_mcp_server.py                                     │
   │ ↓                                                               │
   │ FastMCP Server starts on 0.0.0.0:8000                         │
   │ ↓                                                               │
   │ SSE endpoint available at http://localhost:8000/sse             │
   └─────────────────────────────────────────────────────────────────┘

2. Client Connection:
   ┌─────────────────────────────────────────────────────────────────┐
   │ python azure_openai_mcp_client.py                              │
   │ ↓                                                               │
   │ Client creates TCP connection to localhost:8000                │
   │ ↓                                                               │
   │ HTTP GET request to /sse endpoint                               │
   │ ↓                                                               │
   │ Server responds with SSE stream (text/event-stream)             │
   │ ↓                                                               │
   │ Persistent connection established                               │
   └─────────────────────────────────────────────────────────────────┘

3. Tool Discovery:
   ┌─────────────────────────────────────────────────────────────────┐
   │ Client sends: list_tools() via SSE                             │
   │ ↓                                                               │
   │ Server responds with tool definitions                           │
   │ ↓                                                               │
   │ Client converts to OpenAI function definitions                  │
   └─────────────────────────────────────────────────────────────────┘

4. Azure OpenAI Integration:
   ┌─────────────────────────────────────────────────────────────────┐
   │ User asks Azure OpenAI a question                               │
   │ ↓                                                               │
   │ Azure OpenAI (HTTPS to azure.openai.com)                       │
   │ ↓                                                               │
   │ Returns function calls to Client                                │
   │ ↓                                                               │
   │ Client calls MCP Server tools (via existing SSE connection)    │
   │ ↓                                                               │
   │ Server executes tools locally                                   │
   │ ↓                                                               │
   │ Results sent back to Client via SSE                             │
   │ ↓                                                               │
   │ Client sends results to Azure OpenAI                           │
   │ ↓                                                               │
   │ Azure OpenAI provides final response                            │
   └─────────────────────────────────────────────────────────────────┘
```

### **Connection Details**

- **Protocol**: HTTP with Server-Sent Events (SSE)
- **Port**: 8000
- **Binding**: 0.0.0.0 (all interfaces)
- **Transport**: Persistent TCP connection
- **Message Format**: JSON-RPC over SSE

### **Who Initiates What**

1. **Server Startup**: Manual (`python azure_mcp_server.py`)
2. **Client Connection**: Client initiates TCP connection to server
3. **Tool Discovery**: Client requests available tools from server
4. **User Interaction**: User initiates conversation with Azure OpenAI
5. **Tool Execution**: Azure OpenAI initiates tool calls via client
6. **Local Execution**: Server executes tools on local system

## 🔧 Key Features

### **1. Production-Ready Design**
- Comprehensive error handling
- Graceful dependency management
- Network accessibility
- Self-documenting capabilities

### **2. Multi-Domain Tools**
- **Calculations**: Mathematical operations
- **System Access**: OS and hardware information
- **File Operations**: Persistent storage
- **External APIs**: Weather simulation
- **Real-time Data**: Timestamps and dynamic content

### **3. Extensibility**
- Easy to add new tools with `@mcp.tool()`
- Modular design for different capabilities
- Clear separation of concerns

### **4. Integration-Focused**
- Designed specifically for Azure OpenAI
- Optimized for function calling
- Rich tool descriptions for AI understanding

## 🎯 Usage Patterns

### **Development Mode**
```bash
# Start server
python azure_mcp_server.py

# Server logs show:
🚀 Starting Enhanced MCP Server for Azure OpenAI
📡 Server will be accessible at http://localhost:8000/sse
🔧 Available tools: greet, calculate, get_system_info, save_text_file, read_text_file, get_weather
```

### **Production Deployment**
```bash
# Set production environment
export MCP_SSE_HOST=0.0.0.0
export MCP_SSE_PORT=8000

# Run server
python azure_mcp_server.py
```

## 🌟 Benefits

1. **Rich Capabilities**: 6 different tool categories
2. **Real-time Data**: Timestamps, system info, file operations
3. **Error Handling**: Graceful failure modes
4. **Network Ready**: SSE transport for multiple clients
5. **Self-Documenting**: Resources and prompts for discoverability
6. **Production Focus**: Designed for Azure OpenAI integration

## 🚀 Extension Ideas

### **Add Database Access**
```python
@mcp.tool()
def query_database(query: str) -> str:
    """Execute database query"""
    # Implementation here
    return results
```

### **Add API Integration**
```python
@mcp.tool()
def call_external_api(endpoint: str, data: dict) -> str:
    """Call external REST API"""
    # Implementation here
    return response
```

### **Add Email Capabilities**
```python
@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """Send email notification"""
    # Implementation here
    return status
```

The `azure_mcp_server.py` file demonstrates a complete, production-ready MCP server that provides Azure OpenAI with comprehensive real-world capabilities! 🚀
