# Memento Client Program Flow - Technical Deep Dive

## 🎯 What Does the Client Do?

The Memento client is a **smart orchestrator** that bridges human natural language with structured data operations through multiple network services. It acts as an intermediary between:

- **Human users** (natural language input)
- **Azure OpenAI** (language understanding and tool orchestration)
- **MCP Server** (actual data storage and retrieval)

---

## 🏗️ Architecture Overview for Technical Developers

The system uses a **three-tier architecture** with network communication between components:

```
┌─────────────────────┐    HTTPS/443     ┌──────────────────────┐
│  Memento Client     │─────────────────▶│   Azure OpenAI       │
│  (Python Process)   │                  │   (Cloud Service)    │
└─────────────────────┘                  └──────────────────────┘
           │
           │ HTTP/8000 (SSE)
           ▼
┌─────────────────────┐
│  MCP Server         │
│  (Local Process)    │
└─────────────────────┘
```

### Key Technical Concepts:

1. **MCP (Model Context Protocol)**: A protocol for AI models to interact with external tools and data sources
2. **SSE (Server-Sent Events)**: HTTP-based protocol for real-time communication between client and MCP server
3. **Tool Calling**: OpenAI's function calling feature that allows AI models to execute external functions
4. **Natural Language Processing**: Converting human language to structured API calls

---

## 🔄 The Complete Technical Workflow

### **Phase 1: System Initialization**
```python
# 1. MCP Server starts and binds to port 8000
mcp.run(transport="sse")  # Creates HTTP server listening on 0.0.0.0:8000

# 2. Client connects to MCP server via SSE
sse_client = sse_client("http://localhost:8000/sse")
# TCP connection established: Client → MCP Server (port 8000)

# 3. Client initializes Azure OpenAI connection
azure_client = AzureOpenAI(endpoint="https://your-resource.openai.azure.com")
# HTTPS connection pool ready: Client → Azure OpenAI (port 443)
```

### **Phase 2: User Input Processing**
```
User: "Hey memento, store this meeting summary"
```

**Step 1: 🎤 User Input Reception**
- Client receives natural language input via stdin/UI
- Input is stored as string variable
- No network activity yet

**Step 2: 🧠 Prepare Azure OpenAI Request**
```python
# Client prepares conversation context
messages = [
    {"role": "system", "content": "You are Memento..."},
    {"role": "user", "content": "Hey memento, store this meeting summary"}
]

# Client fetches available tools from MCP server
tools = self.create_tool_definitions()  # Uses existing SSE connection
```

**Step 3: 🌐 Azure OpenAI API Call**
```python
# HTTPS POST request to Azure OpenAI
response = self.azure_client.chat.completions.create(
    model=AZURE_OPENAI_DEPLOYMENT,
    messages=messages,
    tools=tools,          # Available MCP tools
    tool_choice="auto"    # Let AI decide which tools to use
)
```

**Network Traffic:**
```
Client → Azure OpenAI (HTTPS:443)
POST /openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-10-21
Content-Type: application/json
Authorization: Bearer <API_KEY>

{
  "messages": [...],
  "tools": [{"type": "function", "function": {...}}],
  "tool_choice": "auto"
}
```

**Step 4: 🔍 Analyze Azure OpenAI Response**
```python
message = response.choices[0].message

if message.tool_calls:
    # Azure OpenAI decided to use tools
    for tool_call in message.tool_calls:
        tool_name = tool_call.function.name      # "store_memory"
        tool_args = json.loads(tool_call.function.arguments)
```

**Azure OpenAI Response:**
```json
{
  "choices": [{
    "message": {
      "tool_calls": [{
        "id": "call_123",
        "type": "function",
        "function": {
          "name": "store_memory",
          "arguments": "{\"user_id\": \"alice\", \"content\": \"Meeting summary...\"}"
        }
      }]
    }
  }]
}
```

**Step 5: 🔧 Execute MCP Tool**
```python
# Client calls MCP server via existing SSE connection
tool_result = await self.call_mcp_tool(tool_name, tool_args)
```

**Network Traffic:**
```
Client → MCP Server (HTTP:8000 SSE)
POST /tool/store_memory
Content-Type: application/json

{
  "user_id": "alice",
  "content": "Meeting summary about Q4 planning...",
  "description": "Team meeting notes",
  "tags": "work,meeting"
}
```

**MCP Server Response:**
```json
{
  "content": [{
    "type": "text", 
    "text": "Successfully stored 'meeting_summary.txt' for user alice as 20240715_143052_meeting_summary.txt"
  }]
}
```

**Step 6: 📝 Add Tool Results to Conversation**
```python
# Client builds extended conversation context
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
```

**Step 7: 🗣️ Generate Human-Friendly Response**
```python
# Second HTTPS call to Azure OpenAI
final_response = self.azure_client.chat.completions.create(
    model=AZURE_OPENAI_DEPLOYMENT,
    messages=messages  # Now includes tool results
)
```

**Network Traffic:**
```
Client → Azure OpenAI (HTTPS:443)
POST /openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-10-21

{
  "messages": [
    {"role": "system", "content": "You are Memento..."},
    {"role": "user", "content": "Hey memento, store this meeting summary"},
    {"role": "assistant", "tool_calls": [...]},
    {"role": "tool", "content": "Successfully stored 'meeting_summary.txt'..."}
  ]
}
```

**Step 8: 💬 Display Final Response**
```python
final_message = final_response.choices[0].message.content
print(f"\n🧠 Memento: {final_message}")
```

**User sees:**
```
🧠 Memento: I've stored your meeting summary! It's saved with the filename 'meeting_summary.txt' and tagged with 'work' and 'meeting' for easy retrieval later.
```

---

## 🎨 Network Flow Sequence Diagram

```
User          Client          MCP Server      Azure OpenAI
│             │               │               │
│─────────────▶│               │               │
│ "store this" │               │               │
│             │               │               │
│             │◀─────────────▶│               │
│             │  SSE connect  │               │
│             │  (HTTP:8000)  │               │
│             │               │               │
│             │──────────────────────────────▶│
│             │    HTTPS POST (port 443)     │
│             │    /chat/completions         │
│             │    + tools definition        │
│             │               │               │
│             │◀──────────────────────────────│
│             │    tool_calls response       │
│             │               │               │
│             │──────────────▶│               │
│             │ store_memory  │               │
│             │ (SSE/HTTP)    │               │
│             │               │               │
│             │◀──────────────│               │
│             │ success msg   │               │
│             │               │               │
│             │──────────────────────────────▶│
│             │    HTTPS POST (port 443)     │
│             │    /chat/completions         │
│             │    + tool results            │
│             │               │               │
│             │◀──────────────────────────────│
│             │    friendly response         │
│             │               │               │
│◀─────────────│               │               │
│ "I've stored │               │               │
│  your data"  │               │               │
```

---

## � Security & Authentication

### **Azure OpenAI Authentication**
```python
# API Key authentication (Bearer token)
headers = {
    "Authorization": f"Bearer {AZURE_OPENAI_API_KEY}",
    "Content-Type": "application/json"
}
```

### **MCP Server Security**
- **No Authentication**: Local-only communication (localhost:8000)
- **Network Isolation**: Server binds to 0.0.0.0 but typically accessed via localhost
- **User Isolation**: File system level user separation
- **Input Sanitization**: User IDs and filenames are sanitized

### **Firewall Configuration**
```bash
# Required outbound rules for client
iptables -A OUTPUT -p tcp --dport 443 -d *.openai.azure.com -j ACCEPT
iptables -A OUTPUT -p tcp --dport 8000 -d localhost -j ACCEPT

# Required inbound rules for MCP server (if on different machine)
iptables -A INPUT -p tcp --dport 8000 -s <client_ip> -j ACCEPT
```

---

## 📊 Detailed Technical Implementation

### **Phase 1: System Initialization**
```python
class InteractiveMementoMCPClient:
    def __init__(self, mcp_server_url: str = "http://localhost:8000/sse"):
        # Azure OpenAI HTTPS client setup
        self.azure_client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-10-21",
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        
        # MCP connection variables
        self.mcp_server_url = mcp_server_url
        self.mcp_session = None
        self.available_tools = []
        
        # State management
        self.conversation_history = {}  # Per-user conversation storage
        self.current_user = None
```

### **Phase 2: MCP Server Connection**
```python
async def connect_to_mcp(self):
    """Establish SSE connection to MCP server"""
    # Create SSE client connection
    self.sse_client = sse_client(self.mcp_server_url)
    
    # TCP connection establishment
    self.read, self.write = await self.sse_client.__aenter__()
    
    # MCP protocol handshake
    self.mcp_session = ClientSession(self.read, self.write)
    await self.mcp_session.__aenter__()
    await self.mcp_session.initialize()
    
    # Fetch available tools from MCP server
    tools_response = await self.mcp_session.list_tools()
    self.available_tools = tools_response.tools
```

### **Phase 3: Tool Definition Creation**
```python
def create_tool_definitions(self):
    """Convert MCP tools to OpenAI function definitions"""
    tool_definitions = []
    
    for tool in self.available_tools:
        # Create OpenAI-compatible function definition
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
        
        # Add parameter definitions based on tool name
        if tool.name == "store_memory":
            tool_def["function"]["parameters"]["properties"] = {
                "user_id": {"type": "string", "description": "User identifier"},
                "content": {"type": "string", "description": "Content to store"},
                "filename": {"type": "string", "description": "Optional filename"},
                "description": {"type": "string", "description": "Optional description"},
                "tags": {"type": "string", "description": "Comma-separated tags"}
            }
            tool_def["function"]["parameters"]["required"] = ["user_id", "content"]
        
        tool_definitions.append(tool_def)
    
    return tool_definitions
```

### **Phase 4: Azure OpenAI Integration**
```python
async def chat_with_azure_openai(self, user_message: str):
    """Main conversation processing logic"""
    
    # 1. Prepare conversation context
    tools = self.create_tool_definitions()
    messages = [
        {"role": "system", "content": self.get_system_prompt()},
        *self.conversation_history.get(self.current_user, []),
        {"role": "user", "content": user_message}
    ]
    
    # 2. First Azure OpenAI call - understand intent
    response = self.azure_client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    # 3. Process tool calls if any
    message = response.choices[0].message
    if message.tool_calls:
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            # Execute MCP tool
            tool_result = await self.call_mcp_tool(tool_name, tool_args)
            
            # Add to conversation context
            messages.extend([
                {"role": "assistant", "content": None, "tool_calls": [tool_call]},
                {"role": "tool", "tool_call_id": tool_call.id, "content": tool_result}
            ])
        
        # 4. Second Azure OpenAI call - generate response
        final_response = self.azure_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=messages
        )
        
        final_message = final_response.choices[0].message.content
    else:
        final_message = message.content
    
    # 5. Update conversation history
    self.conversation_history.setdefault(self.current_user, []).extend([
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": final_message}
    ])
    
    return final_message
```

### **Phase 5: MCP Tool Execution**
```python
async def call_mcp_tool(self, tool_name: str, arguments: dict):
    """Execute tool on MCP server via SSE connection"""
    try:
        # Send tool call over established SSE connection
        result = await self.mcp_session.call_tool(tool_name, arguments)
        
        # Extract text result from MCP response
        return result.content[0].text
    except Exception as e:
        return f"Error calling tool {tool_name}: {str(e)}"
```

---

## 🚀 Production Considerations

### **Scaling & Performance**
- **Connection Pooling**: Azure OpenAI client uses connection pooling
- **SSE Persistence**: Single persistent connection to MCP server
- **Conversation Management**: In-memory storage (consider Redis for production)
- **Rate Limiting**: Azure OpenAI has rate limits (handle with backoff)

### **Error Handling**
```python
# Network error handling
try:
    response = await self.azure_client.chat.completions.create(...)
except httpx.ReadTimeout:
    return "Azure OpenAI request timed out"
except httpx.ConnectError:
    return "Cannot connect to Azure OpenAI"

# MCP error handling
try:
    result = await self.mcp_session.call_tool(...)
except ConnectionError:
    return "MCP server connection lost"
```

### **Security Hardening**
- **TLS Verification**: Always verify Azure OpenAI certificates
- **API Key Rotation**: Regular API key rotation
- **Input Validation**: Sanitize all user inputs
- **Network Segmentation**: Isolate MCP server if needed

### **Monitoring & Logging**
```python
import logging

# Network request logging
logging.info(f"Azure OpenAI request: {len(messages)} messages")
logging.info(f"MCP tool call: {tool_name} with {len(arguments)} args")
logging.info(f"Response time: {response_time:.2f}s")
```

---

## 🎯 Key Components Explained

### 1. **Tool Definitions** 🛠️
```python
def create_tool_definitions(self):
    # Tells OpenAI what tools are available
    # Like giving OpenAI a menu of actions it can take
    return [
        {
            "type": "function",
            "function": {
                "name": "store_memory",
                "description": "Store content for a user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "content": {"type": "string"}
                    }
                }
            }
        }
    ]
```

### 2. **System Prompt** 📋
```python
def get_system_prompt(self):
    return """You are Memento, a helpful AI assistant...
    When users mention "store this", use the store_memory tool.
    When users ask "what did I store", use retrieve_memories.
    """
```

### 3. **MCP Tool Calling** 🔧
```python
async def call_mcp_tool(self, tool_name: str, arguments: dict):
    # This actually calls the MCP server
    result = await self.mcp_session.call_tool(tool_name, arguments)
    return result.content[0].text
```

---

## 🚀 Example Complete Flow

### User Input:
```
"Hey memento, store this recipe: Chocolate cake with 2 cups flour"
```

### Internal Processing:

1. **Client receives**: `"Hey memento, store this recipe: Chocolate cake with 2 cups flour"`

2. **Client → Azure OpenAI**:
   ```json
   {
     "messages": [
       {"role": "system", "content": "You are Memento..."},
       {"role": "user", "content": "Hey memento, store this recipe: Chocolate cake with 2 cups flour"}
     ],
     "tools": [{"name": "store_memory", ...}]
   }
   ```

3. **Azure OpenAI responds**:
   ```json
   {
     "message": {
       "tool_calls": [
         {
           "function": {
             "name": "store_memory",
             "arguments": "{\"user_id\": \"alice\", \"content\": \"Chocolate cake with 2 cups flour\", \"tags\": \"cooking,recipe\"}"
           }
         }
       ]
     }
   }
   ```

4. **Client → MCP Server**:
   ```python
   await call_mcp_tool("store_memory", {
     "user_id": "alice",
     "content": "Chocolate cake with 2 cups flour",
     "tags": "cooking,recipe"
   })
   ```

5. **MCP Server responds**:
   ```
   "Successfully stored 'recipe.txt' for user alice as 20240715_143052_recipe.txt"
   ```

6. **Client → Azure OpenAI** (with tool results):
   ```json
   {
     "messages": [
       {"role": "system", "content": "You are Memento..."},
       {"role": "user", "content": "Hey memento, store this recipe..."},
       {"role": "assistant", "tool_calls": [...]},
       {"role": "tool", "content": "Successfully stored 'recipe.txt'..."}
     ]
   }
   ```

7. **Azure OpenAI final response**:
   ```
   "I've stored your chocolate cake recipe! It's saved with the tags 'cooking' and 'recipe' so you can easily find it later."
   ```

8. **User sees**:
   ```
   🧠 Memento: I've stored your chocolate cake recipe! It's saved with the tags 'cooking' and 'recipe' so you can easily find it later.
   ```

---

## 🎪 The Magic Behind the Scenes

### Why This Works So Well:

1. **Natural Language Processing**: Azure OpenAI understands human language
2. **Tool Integration**: OpenAI can decide which tools to use
3. **Context Management**: Client maintains conversation history
4. **User Isolation**: Each user has their own conversation and data
5. **Error Handling**: System gracefully handles problems

### The Client is Like a Smart Assistant That:
- 🎧 **Listens** to your natural language
- 🧠 **Thinks** about what you want to do
- 🔧 **Uses tools** to do the actual work
- 💬 **Explains** the results in human terms
- 📝 **Remembers** your conversation

---

## 🔄 State Management

### User State:
```python
self.current_user = "alice"  # Who is using the system
self.users = ["alice", "bob", "charlie"]  # Available users
```

### Conversation State:
```python
self.conversation_history = {
    "alice": [
        {"role": "user", "content": "Store this recipe"},
        {"role": "assistant", "content": "I've stored your recipe!"}
    ],
    "bob": [
        {"role": "user", "content": "What did I store yesterday?"},
        {"role": "assistant", "content": "You stored 3 files yesterday..."}
    ]
}
```

### Connection State:
```python
self.mcp_session = ClientSession(...)  # Connected to MCP server
self.azure_client = AzureOpenAI(...)   # Connected to Azure OpenAI
```

---

## 🌐 Network Architecture & Connection Details

### **TCP Connection Initiation & Firewall Requirements**

#### 1. **Client → Azure OpenAI Connection**
```
Protocol: HTTPS (HTTP over TLS)
Port: 443 (standard HTTPS)
Direction: Outbound from client
Initiator: Memento Client
Target: your-resource.openai.azure.com
```

**Firewall Rules Needed:**
- **Outbound**: Allow client machine to reach `*.openai.azure.com:443`
- **Authentication**: API key-based (no inbound ports required)
- **TLS**: Modern TLS 1.2+ encryption

#### 2. **Client → MCP Server Connection**
```
Protocol: HTTP with Server-Sent Events (SSE)
Port: 8000 (configurable)
Direction: Outbound from client to localhost
Initiator: Memento Client
Target: localhost:8000 or 0.0.0.8000
```

**Firewall Rules Needed:**
- **Local**: Allow connection to localhost:8000
- **Network**: If MCP server runs on different machine, allow inbound 8000
- **Transport**: Plain HTTP (can be upgraded to HTTPS if needed)

#### 3. **Connection Sequence**
```
1. MCP Server starts → Binds to 0.0.0.0:8000 → Listens for connections
2. Client starts → Connects to localhost:8000 → Establishes SSE connection
3. Client initializes → Calls Azure OpenAI → Establishes HTTPS connection
4. User input → Client processes → Makes API calls to both services
```

### **Network Flow Diagram**
```
Internet                    Local Network
    │                           │
    │ HTTPS:443                 │ HTTP:8000
    ▼                           ▼
┌─────────────────┐      ┌─────────────────┐
│   Azure OpenAI  │      │   MCP Server    │
│   (Cloud)       │      │   (localhost)   │
└─────────────────┘      └─────────────────┘
    ▲                           ▲
    │                           │
    │         ┌─────────────────┐         │
    └─────────│  Memento Client │─────────┘
              │  (localhost)    │
              └─────────────────┘
```

---

## 🔌 Connection Establishment Details

### **MCP Server Startup**
```python
# Server binds to all interfaces on port 8000
os.environ["MCP_SSE_HOST"] = "0.0.0.0"  # Accept connections from any IP
os.environ["MCP_SSE_PORT"] = "8000"     # Listen on port 8000
mcp.run(transport="sse")                # Start SSE server
```

### **Client Connection to MCP Server**
```python
# Client creates SSE connection to MCP server
self.sse_client = sse_client("http://localhost:8000/sse")
self.read, self.write = await self.sse_client.__aenter__()

# Establish MCP session
self.mcp_session = ClientSession(self.read, self.write)
await self.mcp_session.initialize()
```

### **Client Connection to Azure OpenAI**
```python
# Client creates HTTPS connection to Azure OpenAI
self.azure_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,           # API authentication
    api_version="2024-10-21",               # API version
    azure_endpoint=AZURE_OPENAI_ENDPOINT   # HTTPS endpoint
)
```

---

## 🎯 Summary

The Memento client is essentially a **smart orchestrator** that bridges:
- **Humans** (who speak natural language)
- **Azure OpenAI** (which understands language and can use tools)
- **MCP Server** (which actually stores and retrieves data)

### **Key Technical Takeaways:**

1. **Network Architecture**: Three-tier system with HTTPS and SSE connections
2. **Protocol Stack**: HTTP/HTTPS for transport, MCP for tool calling, OpenAI API for AI
3. **Security Model**: API key authentication, local MCP server, input sanitization
4. **State Management**: Per-user conversation history and connection pooling
5. **Error Handling**: Graceful degradation across network and service failures

This architecture demonstrates how modern AI systems can provide intuitive natural language interfaces while maintaining robust, scalable, and secure backend systems! 🌟

---

## 📚 Further Reading

- **MCP Protocol**: [Model Context Protocol Specification](https://github.com/modelcontextprotocol/python-sdk)
- **Azure OpenAI**: [Azure OpenAI Service Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)
- **Server-Sent Events**: [MDN SSE Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- **Function Calling**: [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
