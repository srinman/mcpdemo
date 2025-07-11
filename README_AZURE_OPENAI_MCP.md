# Azure OpenAI + MCP Integration Example

This example demonstrates how **Azure OpenAI** can leverage **MCP (Model Context Protocol)** servers to enhance its capabilities with real-time tools and data.

## 🎯 What This Example Shows

**Azure OpenAI** uses your MCP server as a **tool provider**, allowing it to:
- Perform calculations
- Read and write files
- Get system information
- Access weather data (simulated)
- Provide real-time greetings with timestamps

## 🏗️ Architecture

```
┌─────────────────┐    HTTP/JSON    ┌─────────────────┐    SSE/JSON-RPC    ┌─────────────────┐
│   Azure OpenAI  │ ◄─────────────► │   Your Client   │ ◄─────────────────► │   MCP Server    │
│   (GPT-4o-mini) │   Function      │  (Python App)   │   Tool Calls        │  (Local Tools)  │
└─────────────────┘   Calling       └─────────────────┘                     └─────────────────┘
         │                                     │                                       │
         │                                     │                                       │
    ┌─────────┐                         ┌─────────────┐                        ┌─────────────┐
    │ OpenAI  │                         │ MCP Client  │                        │ MCP Tools   │
    │Function │                         │ (sse_client)│                        │ - greet()   │
    │ Calling │                         │             │                        │ - calculate │
    └─────────┘                         └─────────────┘                        │ - files     │
                                                                               │ - weather   │
                                                                               └─────────────┘
```

## 🔄 How It Works

1. **User** asks Azure OpenAI a question
2. **Azure OpenAI** determines it needs tools to answer
3. **Client** receives function calls from Azure OpenAI
4. **Client** calls MCP server tools via SSE
5. **MCP Server** executes tools and returns results
6. **Client** sends results back to Azure OpenAI
7. **Azure OpenAI** provides final answer to user

## 📁 Files Overview

### Core Files:
- `azure_mcp_server.py` - Enhanced MCP server with useful tools
- `azure_openai_mcp_client.py` - Azure OpenAI client that uses MCP tools
- `setup.py` - Setup script for configuration

### Original Examples:
- `server.py` / `client.py` - Basic local MCP example
- `servernetwork.py` / `clientnetwork.py` - Basic network MCP example

## 🚀 Quick Start

### 1. Setup
```bash
# Install dependencies
pip install openai mcp psutil

# Run setup script
python setup.py
```

### 2. Configure Azure OpenAI
Edit `.env` file with your credentials:
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

### 3. Start MCP Server
```bash
python azure_mcp_server.py
```

### 4. Run Azure OpenAI Client
```bash
python azure_openai_mcp_client.py
```

## 🎭 Demo Mode

If you don't have Azure OpenAI credentials, the client runs in **demo mode** showing simulated interactions:

```
🎭 DEMO MODE - Simulated Azure OpenAI + MCP interaction:
💬 User: Calculate 15 + 25 and then save the result to a file
🔧 Azure OpenAI would call: calculate(operation='add', a=15, b=25)
📋 MCP Result: Result: 15.0 add 25.0 = 40.0
🔧 Azure OpenAI would call: save_text_file(filename='calculation.txt', content='15 + 25 = 40')
📋 MCP Result: Successfully saved content to calculation.txt
🤖 Azure OpenAI: I've calculated 15 + 25 = 40 and saved the result to calculation.txt
```

## 🔧 Available MCP Tools

The enhanced MCP server provides these tools to Azure OpenAI:

### 1. **greet(name)** - Personalized greeting
- Returns greeting with timestamp
- Example: "Hello Azure OpenAI! Current time: 2025-01-11 10:30:45"

### 2. **calculate(operation, a, b)** - Mathematical operations
- Supports: add, subtract, multiply, divide
- Example: `calculate("multiply", 15, 8)` → "Result: 15.0 multiply 8.0 = 120.0"

### 3. **get_system_info()** - System information
- Returns OS, CPU, memory details as JSON
- Useful for system monitoring queries

### 4. **save_text_file(filename, content)** - File writing
- Saves text content to files
- Example: `save_text_file("note.txt", "Hello World")`

### 5. **read_text_file(filename)** - File reading
- Reads and returns file content
- Example: `read_text_file("note.txt")`

### 6. **get_weather(city)** - Weather information
- Returns mock weather data
- Example: `get_weather("San Francisco")` → "Weather in San Francisco: 72°F, sunny"

## 💬 Example Conversations

### Simple Calculation:
```
User: "What's 15 times 8?"
Azure OpenAI: [calls calculate("multiply", 15, 8)]
MCP Result: "Result: 15.0 multiply 8.0 = 120.0"
Azure OpenAI: "15 times 8 equals 120."
```

### File Operations:
```
User: "Save 'Hello MCP' to a file called greeting.txt"
Azure OpenAI: [calls save_text_file("greeting.txt", "Hello MCP")]
MCP Result: "Successfully saved content to greeting.txt"
Azure OpenAI: "I've saved 'Hello MCP' to greeting.txt for you."
```

### Multi-step Operations:
```
User: "Calculate 100 divided by 4, then save the result to math.txt"
Azure OpenAI: [calls calculate("divide", 100, 4)]
MCP Result: "Result: 100.0 divide 4.0 = 25.0"
Azure OpenAI: [calls save_text_file("math.txt", "100 ÷ 4 = 25")]
MCP Result: "Successfully saved content to math.txt"
Azure OpenAI: "I calculated 100 ÷ 4 = 25 and saved the result to math.txt."
```

## 🔗 Key Concepts

### **MCP Tools as OpenAI Functions**
- MCP tools become OpenAI function definitions
- Azure OpenAI can call these functions automatically
- Results are seamlessly integrated into conversations

### **Real-time Capabilities**
- MCP provides real-time data (timestamps, system info)
- Azure OpenAI gets fresh information, not training data
- Tools can perform actions (file operations, calculations)

### **Extensibility**
- Easy to add new tools to MCP server
- Azure OpenAI automatically discovers new capabilities
- No need to retrain models

## 🌟 Benefits of Azure OpenAI + MCP

1. **Enhanced Capabilities**: Azure OpenAI gains access to real-time tools
2. **Flexibility**: Easy to add new tools without changing AI model
3. **Security**: Tools run locally, sensitive data stays local
4. **Reliability**: Network-based architecture for distributed systems
5. **Scalability**: Multiple clients can use the same MCP server

## 🛠️ Extending the Example

### Add New Tools:
```python
@mcp.tool()
def your_custom_tool(param: str) -> str:
    """Your custom tool description"""
    # Your implementation here
    return f"Result: {param}"
```

### Add Tool to Azure OpenAI:
```python
# Tool definition gets automatically created
# based on your MCP tool registration
```

## 📚 Next Steps

1. **Add Real APIs**: Replace mock weather with real weather API
2. **Database Integration**: Add database read/write tools
3. **Authentication**: Add security for production use
4. **Monitoring**: Add logging and metrics
5. **Scaling**: Deploy MCP server to cloud

This example demonstrates the power of combining Azure OpenAI's intelligence with MCP's tool ecosystem! 🚀
