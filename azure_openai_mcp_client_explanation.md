# Azure OpenAI MCP Client Code Explanation

This document provides a detailed explanation of `azure_openai_mcp_client.py` - the Python code that integrates Azure OpenAI with MCP (Model Context Protocol) servers.

## 🎯 What This Code Does

The `azure_openai_mcp_client.py` file creates a **bridge** between Azure OpenAI's function calling capabilities and MCP server tools. It allows Azure OpenAI to:

1. **Discover** MCP tools automatically
2. **Call** MCP tools through function calling
3. **Use** real-time tool results in conversations

## 🏗️ Client Architecture

```
┌─────────────────┐    HTTPS/JSON    ┌─────────────────┐    HTTP/SSE      ┌─────────────────┐
│   Azure OpenAI  │ ◄─────────────► │   MCP Client    │ ◄─────────────► │   MCP Server    │
│   (Cloud API)   │   Function       │ (azure_openai_  │   Tool Calls     │ (localhost:8000)│
│                 │   Calling        │  mcp_client.py) │                  │                 │
└─────────────────┘                  └─────────────────┘                  └─────────────────┘
         │                                     │                                     │
         │          Internet                   │           Network                   │
         │ ◄─────────────────────────────────► │ ◄─────────────────────────────────► │
    OpenAI Service                      Python Client                       Local Tools
    (Function calls)                    (Bridge/Proxy)                    (Real execution)
```

## � Connection Establishment Details

### 1. MCP Server Connection:
```
Client                    Network                    MCP Server
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
  │ 4. Server Info          │                         │
  │◄────────────────────────│◄────────────────────────│
  │                         │                         │
  │ 5. List Tools           │                         │
  │────────────────────────►│────────────────────────►│
  │                         │                         │
  │ 6. Tool Definitions     │                         │
  │◄────────────────────────│◄────────────────────────│
```

### 2. Azure OpenAI Connection:
```
Client                    Internet                   Azure OpenAI
  │                         │                         │
  │ 1. HTTPS Request        │                         │
  │────────────────────────►│────────────────────────►│
  │                         │                         │
  │ 2. Authentication       │                         │
  │────────────────────────►│────────────────────────►│
  │                         │                         │
  │ 3. Function Definitions │                         │
  │────────────────────────►│────────────────────────►│
  │                         │                         │
  │ 4. Chat Response        │                         │
  │◄────────────────────────│◄────────────────────────│
```

### 3. Tool Mapping Process:
```
MCP Tools                Function Definitions         Azure OpenAI
    │                          │                          │
    │ 1. greet(name)           │                          │
    │─────────────────────────►│                          │
    │                          │                          │
    │                          │ 2. OpenAI Function       │
    │                          │ {                        │
    │                          │   "name": "greet",       │
    │                          │   "parameters": {...}    │
    │                          │ }                        │
    │                          │─────────────────────────►│
    │                          │                          │
    │ 3. calculate(op,a,b)     │                          │
    │─────────────────────────►│                          │
    │                          │                          │
    │                          │ 4. OpenAI Function       │
    │                          │ {                        │
    │                          │   "name": "calculate",   │
    │                          │   "parameters": {...}    │
    │                          │ }                        │
    │                          │─────────────────────────►│
```

## �🔄 Complete Integration Flow

### System Initialization:
1. **Environment Setup**: Load .env file and Azure OpenAI credentials
2. **MCP Connection**: Establish SSE connection to local MCP server
3. **Tool Discovery**: List available tools from MCP server
4. **Function Mapping**: Convert MCP tools to OpenAI function definitions
5. **Client Ready**: System ready for user interactions

### User Interaction Sequence:
```
User                Azure OpenAI           Client                 MCP Server           Local System
  │                      │                   │                       │                     │
  │ 1. User Question     │                   │                       │                     │
  │─────────────────────►│                   │                       │                     │
  │                      │                   │                       │                     │
  │                      │ 2. Analyze + Tools│                       │                     │
  │                      │──────────────────►│                       │                     │
  │                      │                   │                       │                     │
  │                      │ 3. Function Calls │                       │                     │
  │                      │──────────────────►│                       │                     │
  │                      │                   │                       │                     │
  │                      │                   │ 4. MCP Tool Call      │                     │
  │                      │                   │──────────────────────►│                     │
  │                      │                   │                       │                     │
  │                      │                   │                       │ 5. Execute Tool     │
  │                      │                   │                       │────────────────────►│
  │                      │                   │                       │                     │
  │                      │                   │                       │ 6. Tool Result      │
  │                      │                   │                       │◄────────────────────│
  │                      │                   │                       │                     │
  │                      │                   │ 7. Tool Response      │                     │
  │                      │                   │◄──────────────────────│                     │
  │                      │                   │                       │                     │
  │                      │ 8. Tool Results   │                       │                     │
  │                      │◄──────────────────│                       │                     │
  │                      │                   │                       │                     │
  │                      │ 9. Generate Response                      │                     │
  │                      │──────────────────►│                       │                     │
  │                      │                   │                       │                     │
  │ 10. Final Answer     │                   │                       │                     │
  │◄─────────────────────│                   │                       │                     │
```

### Multi-Step Tool Execution:
```
User: "Calculate 25 * 4 and save the result to math.txt"

User                Azure OpenAI           Client                 MCP Server
  │                      │                   │                       │
  │ Complex request      │                   │                       │
  │─────────────────────►│                   │                       │
  │                      │                   │                       │
  │                      │ Function: calc()  │                       │
  │                      │──────────────────►│                       │
  │                      │                   │                       │
  │                      │                   │ calculate(25, 4)      │
  │                      │                   │──────────────────────►│
  │                      │                   │                       │
  │                      │                   │ Result: 100           │
  │                      │                   │◄──────────────────────│
  │                      │                   │                       │
  │                      │ Result: 100       │                       │
  │                      │◄──────────────────│                       │
  │                      │                   │                       │
  │                      │ Function: save()  │                       │
  │                      │──────────────────►│                       │
  │                      │                   │                       │
  │                      │                   │ save_file(math.txt)   │
  │                      │                   │──────────────────────►│
  │                      │                   │                       │
  │                      │                   │ File saved            │
  │                      │                   │◄──────────────────────│
  │                      │                   │                       │
  │                      │ File saved        │                       │
  │                      │◄──────────────────│                       │
  │                      │                   │                       │
  │                      │ Generate final    │                       │
  │                      │ response          │                       │
  │                      │──────────────────►│                       │
  │                      │                   │                       │
  │ "I calculated 25*4=100│                   │                       │
  │ and saved to math.txt"│                   │                       │
  │◄─────────────────────│                   │                       │
```

## 🌐 Transport Protocol Analysis

### Dual Network Architecture:
```
Internet (HTTPS)          Local Network (HTTP/SSE)
     │                           │
     │ ◄─── Azure OpenAI ───────►│ ◄─── MCP Client ───────►│ ◄─── MCP Server
     │      (Cloud API)          │      (Bridge)           │      (Local Tools)
     │                           │                         │
 Encrypted                   Unencrypted               Direct calls
 Remote calls               Local calls                System access
```

### Protocol Comparison:
| Aspect | Azure OpenAI Connection | MCP Server Connection |
|--------|-------------------------|----------------------|
| **Protocol** | HTTPS/TLS | HTTP/SSE |
| **Security** | Encrypted | Local network |
| **Location** | Cloud/Internet | localhost:8000 |
| **Format** | JSON/REST | JSON-RPC/SSE |
| **Purpose** | AI inference | Tool execution |
| **Latency** | Higher (network) | Lower (local) |
| **Bandwidth** | Metered | Unlimited |

### Message Flow Types:
```
1. User → Client → Azure OpenAI (Question)
   └─ Format: REST API call with function definitions

2. Azure OpenAI → Client (Function calls)
   └─ Format: JSON with tool_calls array

3. Client → MCP Server (Tool execution)
   └─ Format: JSON-RPC over SSE

4. MCP Server → Client (Tool results)
   └─ Format: JSON-RPC response

5. Client → Azure OpenAI (Tool results)
   └─ Format: REST API with tool results

6. Azure OpenAI → Client → User (Final answer)
   └─ Format: Natural language response
```

## 📨 Network Protocol Details

### Azure OpenAI API Call:
```http
POST /openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-10-21 HTTP/1.1
Host: your-resource.openai.azure.com
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "messages": [
    {
      "role": "user",
      "content": "Calculate 15 * 8"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "calculate",
        "description": "Perform mathematical operations",
        "parameters": {
          "type": "object",
          "properties": {
            "operation": {"type": "string"},
            "a": {"type": "number"},
            "b": {"type": "number"}
          },
          "required": ["operation", "a", "b"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

### Azure OpenAI Function Call Response:
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "calculate",
              "arguments": "{\"operation\": \"multiply\", \"a\": 15, \"b\": 8}"
            }
          }
        ]
      }
    }
  ]
}
```

### MCP Tool Call (to Local Server):
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

### Final Azure OpenAI Response:
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "15 times 8 equals 120."
      }
    }
  ]
}
```

## 📋 Code Structure Breakdown

### 1. **Environment Setup & Configuration**

```python
# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("   Or set environment variables manually")

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-resource.openai.azure.com")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "your-api-key")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
```

**Purpose**: 
- Loads Azure OpenAI credentials from `.env` file
- Provides fallback defaults for demo mode
- Handles missing `python-dotenv` dependency gracefully

### 2. **AzureOpenAIMCPClient Class**

This is the main class that handles all integration logic:

#### **Constructor (`__init__`)**

```python
def __init__(self, mcp_server_url: str = "http://localhost:8000/sse"):
    self.mcp_server_url = mcp_server_url
    self.azure_client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version="2024-10-21",
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    self.mcp_session = None
    self.available_tools = []
```

**Purpose**: 
- Initializes Azure OpenAI client with credentials
- Sets up MCP server connection URL
- Prepares storage for MCP tools

#### **MCP Connection (`connect_to_mcp`)**

```python
async def connect_to_mcp(self):
    """Connect to the MCP server and get available tools"""
    print("🔗 Connecting to MCP server...")
    self.sse_client = sse_client(self.mcp_server_url)
    self.read, self.write = await self.sse_client.__aenter__()
    
    self.mcp_session = ClientSession(self.read, self.write)
    await self.mcp_session.__aenter__()
    await self.mcp_session.initialize()
    
    # Get available tools
    tools_response = await self.mcp_session.list_tools()
    self.available_tools = tools_response.tools
    
    print(f"✅ Connected to MCP server with {len(self.available_tools)} tools")
```

**Purpose**: 
- Establishes SSE connection to MCP server
- Initializes MCP session
- Discovers available tools from the server
- Stores tools for later use

#### **Tool Execution (`call_mcp_tool`)**

```python
async def call_mcp_tool(self, tool_name: str, arguments: dict):
    """Call a tool on the MCP server"""
    try:
        result = await self.mcp_session.call_tool(tool_name, arguments)
        return result.content[0].text
    except Exception as e:
        return f"Error calling tool {tool_name}: {str(e)}"
```

**Purpose**: 
- Executes MCP tools with given arguments
- Returns tool results or error messages
- Handles exceptions gracefully

#### **Tool Definition Creation (`create_tool_definitions`)**

```python
def create_tool_definitions(self):
    """Create OpenAI function definitions from MCP tools"""
    tool_definitions = []
    
    for tool in self.available_tools:
        # Create a simplified tool definition for Azure OpenAI
        tool_def = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
        
        # Add parameter definitions based on tool names
        if tool.name == "calculate":
            tool_def["function"]["parameters"]["properties"].update({
                "operation": {
                    "type": "string",
                    "description": "Mathematical operation (add, subtract, multiply, divide)"
                },
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            })
            tool_def["function"]["parameters"]["required"] = ["operation", "a", "b"]
        # ... similar for other tools
```

**Purpose**: 
- Converts MCP tool definitions to OpenAI function format
- Maps tool parameters to OpenAI function parameters
- Handles different tool types (calculate, file operations, etc.)

**Key Insight**: This is where MCP tools become Azure OpenAI functions!

#### **Chat Integration (`chat_with_tools`)**

```python
async def chat_with_tools(self, user_message: str):
    """Chat with Azure OpenAI using MCP tools"""
    print(f"\n💬 User: {user_message}")
    
    # Get tool definitions
    tools = self.create_tool_definitions()
    
    # Create initial message
    messages = [
        {
            "role": "system",
            "content": """You are a helpful assistant that can use various tools..."""
        },
        {
            "role": "user",
            "content": user_message
        }
    ]
    
    # Call Azure OpenAI
    response = self.azure_client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
```

**Purpose**: 
- Orchestrates the conversation flow
- Sends tool definitions to Azure OpenAI
- Processes Azure OpenAI responses
- Handles tool calls and results

### 3. **Tool Call Processing**

```python
if message.tool_calls:
    print("🔧 Azure OpenAI wants to use tools:")
    
    # Execute tool calls
    for tool_call in message.tool_calls:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        
        print(f"  📞 Calling {tool_name} with args: {tool_args}")
        
        # Call the MCP tool
        tool_result = await self.call_mcp_tool(tool_name, tool_args)
        print(f"  📋 Result: {tool_result}")
        
        # Add tool result to conversation
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [tool_call]
        })
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": tool_result
        })
    
    # Get final response from Azure OpenAI
    final_response = self.azure_client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=messages
    )
```

**Purpose**: 
- Processes each tool call from Azure OpenAI
- Executes MCP tools and collects results
- Adds tool results to conversation history
- Gets final response from Azure OpenAI

### 4. **Main Demo Function**

```python
async def main():
    """Main demo function"""
    print("🚀 Azure OpenAI + MCP Integration Demo")
    print("=" * 50)
    
    # Check if environment variables are set
    if AZURE_OPENAI_API_KEY == "your-api-key":
        # Demo mode - simulated interaction
        print("\n🎭 DEMO MODE - Simulated Azure OpenAI + MCP interaction:")
        # ... show simulated interaction
        return
    
    # Initialize the client
    client = AzureOpenAIMCPClient()
    
    try:
        # Connect to MCP server
        await client.connect_to_mcp()
        
        # Demo conversations
        demo_messages = [
            "Hello! Can you greet me and tell me what time it is?",
            "Calculate 15 * 8 for me",
            "What's the weather like in San Francisco?",
            "Save a message 'Hello from Azure OpenAI + MCP!' to a file called 'demo.txt'",
            "Now read that file back to me",
            "Can you get system information about this computer?"
        ]
        
        for message in demo_messages:
            await client.chat_with_tools(message)
            await asyncio.sleep(1)
```

**Purpose**: 
- Provides demo mode when credentials aren't available
- Runs a series of test conversations
- Shows real Azure OpenAI + MCP integration

## 🔄 Execution Flow

### **Complete Interaction Example:**

1. **User Input**: "Calculate 15 * 8"
2. **Client**: Creates tool definitions from MCP tools
3. **Azure OpenAI**: Receives tools and user message
4. **Azure OpenAI**: Decides to call `calculate` function
5. **Azure OpenAI**: Returns function call: `calculate(operation="multiply", a=15, b=8)`
6. **Client**: Receives function call
7. **Client**: Calls MCP server: `await call_mcp_tool("calculate", {"operation": "multiply", "a": 15, "b": 8})`
8. **MCP Server**: Executes calculation and returns: "Result: 15.0 multiply 8.0 = 120.0"
9. **Client**: Sends result back to Azure OpenAI
10. **Azure OpenAI**: Processes result and responds: "15 times 8 equals 120."

## 🎯 Key Features

### **1. Automatic Tool Discovery**
- MCP tools are automatically discovered
- No manual configuration needed
- Tools become available to Azure OpenAI instantly

### **2. Flexible Tool Mapping**
- Different tool types handled appropriately
- Parameter mapping from MCP to OpenAI format
- Graceful error handling

### **3. Demo Mode**
- Works without Azure OpenAI credentials
- Shows simulated interactions
- Perfect for learning and testing

### **4. Environment Configuration**
- Reads from `.env` file
- Fallback to environment variables
- Clear error messages for missing dependencies

## 🔧 Extensibility

### **Adding New Tools**
To add support for a new MCP tool:

1. Add it to the MCP server
2. Add parameter mapping in `create_tool_definitions()`
3. No other changes needed!

### **Example: Adding a Database Tool**
```python
# In create_tool_definitions()
elif tool.name == "query_database":
    tool_def["function"]["parameters"]["properties"]["query"] = {
        "type": "string",
        "description": "SQL query to execute"
    }
    tool_def["function"]["parameters"]["required"] = ["query"]
```

## 🚀 Benefits of This Architecture

1. **Separation of Concerns**: Azure OpenAI handles AI, MCP handles tools
2. **Scalability**: Multiple clients can use the same MCP server
3. **Flexibility**: Easy to add new tools without changing AI code
4. **Security**: Tools run locally with controlled access
5. **Reliability**: Graceful error handling and fallbacks

## 🎓 Learning Value

This code demonstrates:
- **Async programming** with Python
- **Integration patterns** for AI and tools
- **Error handling** in network applications
- **Configuration management** with environment variables
- **Protocol bridging** between different systems

The `azure_openai_mcp_client.py` file is a complete example of how to create a production-ready integration between Azure OpenAI and MCP servers! 🚀
