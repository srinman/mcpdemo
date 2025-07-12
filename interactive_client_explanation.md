# Interactive MCP Client Code Explanation

This document provides a detailed explanation of `interactive_client.py` - a practical example showing how MCP prompts work in real applications.

## 🎯 What This Code Demonstrates

The `interactive_client.py` file shows the **normal usage pattern** for MCP prompts in a real application. It demonstrates how client applications typically:

1. **Discover** available prompts from the server
2. **Present** them to users for selection
3. **Retrieve** the selected prompt content
4. **Guide** user interactions with prompt suggestions

## 🏗️ Application Architecture

```
┌─────────────────┐    stdio/JSON-RPC    ┌─────────────────┐
│  Interactive    │ ◄─────────────────► │   MCP Server    │
│  Client UI      │   Tool/Resource      │   (server.py)   │
│  (Menu System)  │   /Prompt Calls      │                 │
└─────────────────┘                      └─────────────────┘
         │                                         │
         │         User Interface                  │
         │ ◄─────────────────────────────────────► │
    Console Menu                            Local execution
    (User choices)                         (Tools, Resources, 
                                           Prompts)
```

## 📋 Code Structure Breakdown

### **1. Main Application Loop**

```python
while True:
    print("\n📋 What would you like to do?")
    print("1. Use a tool directly")
    print("2. Get helpful prompts") 
    print("3. Check server info")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
```

**Purpose**: 
- Creates a persistent interactive session
- Provides clear menu options for different MCP capabilities
- Demonstrates real-world application flow

**Key Insight**: This is how **real MCP applications** work - they provide ongoing interaction rather than single-use calls.

### **2. Direct Tool Usage (Option 1)**

```python
if choice == "1":
    # Direct tool usage
    print("\n🔧 Available tools:")
    tools = await session.list_tools()
    for i, tool in enumerate(tools.tools, 1):
        print(f"   {i}. {tool.name} - {tool.description}")
    
    name = input("\nEnter a name to greet: ").strip()
    if name:
        result = await session.call_tool("greet", {"name": name})
        print(f"   🎉 {result.content[0].text}")
```

**Purpose**: 
- Shows **tool discovery** and **direct usage**
- Demonstrates how applications can list available tools
- Provides immediate tool execution based on user input

**Real-world Usage**: 
- Developer tools that need to call specific MCP functions
- Administrative interfaces for MCP server management
- Testing and debugging applications

### **3. Prompt-Guided Interaction (Option 2) - THE KEY FEATURE**

This is the **most important section** that demonstrates how MCP prompts work in practice:

```python
elif choice == "2":
    # PROMPT USAGE - This is the normal pattern!
    print("\n💡 Getting helpful prompts from server...")
    
    # 1. Discovery: Get available prompts
    prompts = await session.list_prompts()
    
    if not prompts.prompts:
        print("   No prompts available from server.")
        continue
    
    # 2. User Selection: Show prompts and let user choose
    print(f"\n📝 Available prompts ({len(prompts.prompts)}):")
    for i, prompt in enumerate(prompts.prompts, 1):
        print(f"   {i}. {prompt.description}")
    
    try:
        selection = int(input(f"\nSelect prompt (1-{len(prompts.prompts)}): ")) - 1
        if 0 <= selection < len(prompts.prompts):
            selected_prompt = prompts.prompts[selection]
            
            # 3. Prompt Retrieval: Get the selected prompt
            prompt_result = await session.get_prompt(selected_prompt.name)
            prompt_text = prompt_result.messages[0].content.text
            
            # 4. User Interaction: Show prompt and guide user
            print(f"\n💭 Prompt: {prompt_text}")
            print("   (This prompt suggests what you might want to ask)")
            
            # In a real UI, this would help guide the user's next input
            user_response = input("\nYour response: ").strip()
            if user_response:
                # Use the response with a tool
                result = await session.call_tool("greet", {"name": user_response})
                print(f"   🎉 {result.content[0].text}")
        else:
            print("   Invalid selection.")
    except ValueError:
        print("   Please enter a valid number.")
```

**This demonstrates the complete MCP prompt workflow**:

#### **Phase 1: Discovery (App-controlled)**
```python
prompts = await session.list_prompts()
```
- Application automatically discovers available prompts
- No user interaction needed at this stage
- Similar to how apps discover available tools

#### **Phase 2: User Selection (User-controlled)**
```python
print(f"\n📝 Available prompts ({len(prompts.prompts)}):")
for i, prompt in enumerate(prompts.prompts, 1):
    print(f"   {i}. {prompt.description}")
```
- **User sees available prompt options**
- **User chooses which prompt they want**
- This is the **"user-controlled"** aspect

#### **Phase 3: Prompt Retrieval (App-controlled)**
```python
prompt_result = await session.get_prompt(selected_prompt.name)
prompt_text = prompt_result.messages[0].content.text
```
- Application fetches the actual prompt content
- Happens automatically after user selection

#### **Phase 4: User Guidance (User-controlled)**
```python
print(f"\n💭 Prompt: {prompt_text}")
print("   (This prompt suggests what you might want to ask)")
user_response = input("\nYour response: ").strip()
```
- **User sees the helpful prompt text**
- **User uses the prompt to guide their input**
- This is where prompts provide real value

### **4. Resource Information (Option 3)**

```python
elif choice == "3":
    # Resource usage
    print("\n📚 Server Information:")
    resource_result = await session.read_resource("info://version")
    print(f"   Version: {resource_result.contents[0].text}")
```

**Purpose**: 
- Demonstrates **resource access** for server information
- Shows how apps can get server metadata
- Provides context about server capabilities

## 🌟 Why MCP Prompts Are Useful - Real-World Scenarios

### **1. User Onboarding**
```python
# Server provides onboarding prompts
@mcp.prompt(description="Get started with this MCP server")
def getting_started() -> str:
    return "Welcome! Try asking me to greet someone or check my version info."
```

**Client Usage**: New users select "Get started" → See helpful guidance → Know what to try first

### **2. Feature Discovery**
```python
# Server suggests available features
@mcp.prompt(description="Discover what I can do")
def feature_discovery() -> str:
    return "I can perform calculations, file operations, and system queries. What would you like to try?"
```

**Client Usage**: Users unsure what's available → Select "Discover features" → Learn about capabilities

### **3. Context-Specific Guidance**
```python
# Server provides context-aware suggestions
@mcp.prompt(description="Help with file operations")
def file_help() -> str:
    return "I can read, write, and list files. What file operation do you need help with?"
```

**Client Usage**: Users working with files → Select "File help" → Get specific guidance

### **4. Error Recovery**
```python
# Server suggests recovery actions
@mcp.prompt(description="Troubleshoot common issues")
def troubleshooting() -> str:
    return "Having problems? Try checking your file permissions or verify the file path exists."
```

**Client Usage**: Users encountering errors → Select "Troubleshoot" → Get recovery suggestions

## 🔄 Complete User Flow Example

Here's how a typical interaction works:

```
1. User runs: python interactive_client.py
   
2. User sees menu:
   📋 What would you like to do?
   1. Use a tool directly
   2. Get helpful prompts
   3. Check server info
   4. Exit

3. User selects: 2 (Get helpful prompts)

4. Client discovers and shows prompts:
   📝 Available prompts (3):
   1. Prompt asking for a name to greet
   2. Suggest trying a friendly greeting
   3. Ask about server capabilities

5. User selects: 2 (Suggest trying a friendly greeting)

6. Client retrieves and shows prompt:
   💭 Prompt: Try asking me to greet someone! I can say hello to anyone you'd like.
   (This prompt suggests what you might want to ask)

7. User responds: Alice

8. Client uses response with tool:
   🎉 Hello Hello, Alice!
```

## 🎯 Key Benefits Demonstrated

### **1. Discoverability**
- Users learn what the server can do
- No need to read documentation
- Self-guiding interface

### **2. User Experience**
- Clear guidance on what to try
- Reduces user confusion
- Provides contextual help

### **3. Dynamic Guidance**
- Server can update prompts without client changes
- Context-aware suggestions
- Adaptive user interface

### **4. Separation of Concerns**
- Server provides domain expertise (prompts)
- Client handles user interaction (menu)
- Clean architectural separation

## 🚀 Real-World Applications

### **1. Developer Tools**
```python
# IDE integration
@mcp.prompt(description="Code analysis suggestions")
def code_analysis() -> str:
    return "I can analyze your code for bugs, performance issues, or style problems. What would you like me to check?"
```

### **2. System Administration**
```python
# Server management
@mcp.prompt(description="System health check")
def health_check() -> str:
    return "I can check CPU, memory, disk usage, and running processes. What system aspect concerns you?"
```

### **3. Data Analysis**
```python
# Analytics platform
@mcp.prompt(description="Data visualization options")
def data_viz() -> str:
    return "I can create charts, graphs, and reports from your data. What type of visualization do you need?"
```

### **4. Content Creation**
```python
# Writing assistant
@mcp.prompt(description="Writing help")
def writing_help() -> str:
    return "I can help with grammar, style, structure, or brainstorming. What writing task can I assist with?"
```

## 🔧 Technical Implementation Details

### **Error Handling**
- Graceful handling of invalid user input
- Proper exception handling for network issues
- User-friendly error messages

### **Session Management**
- Persistent connection throughout user session
- Proper cleanup on exit
- State management across interactions

### **User Interface**
- Clear menu structure
- Intuitive prompt presentation
- Responsive feedback

## 🌟 Extension Ideas

### **1. Prompt Categories**
```python
# Organize prompts by category
prompts_by_category = {
    "Getting Started": [...],
    "Advanced Features": [...],
    "Troubleshooting": [...]
}
```

### **2. Prompt History**
```python
# Remember recently used prompts
recent_prompts = []
# Show "Recently used" section
```

### **3. Contextual Prompts**
```python
# Show different prompts based on current state
if user_is_new:
    show_onboarding_prompts()
elif user_has_error:
    show_troubleshooting_prompts()
```

### **4. Prompt Chaining**
```python
# Link prompts together for complex workflows
@mcp.prompt(description="Multi-step file operation")
def file_workflow() -> str:
    return "Let's work with files step by step. First, what file do you want to work with?"
```

## 🎉 Conclusion

The `interactive_client.py` demonstrates that **MCP prompts are a powerful UX feature** that:

1. **Help users discover** what an MCP server can do
2. **Guide user interactions** with helpful suggestions
3. **Provide context-aware assistance** for complex tasks
4. **Enable self-documenting servers** that explain their own capabilities

This pattern is essential for creating user-friendly MCP applications that don't require extensive documentation or training to use effectively! 🚀

## 🔗 Related Files

- [`server.py`](server.py) - The MCP server with multiple prompts
- [`interactive_client.py`](interactive_client.py) - This client implementation
- [`MCP_LEARNING_JOURNEY.md`](MCP_LEARNING_JOURNEY.md) - Complete learning path
- [`client_explanation.md`](client_explanation.md) - Basic client explanation
