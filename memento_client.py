#!/usr/bin/env python3
"""
Memento: AI Memory - Interactive Client
Azure OpenAI integration with Memento MCP server for intelligent memory management.

Catchphrase: "Hey Memento" - Your AI memory assistant
"""

import asyncio
import os
import json
from datetime import datetime
from mcp.client.stdio import stdio_client
from mcp import ClientSession
from openai import AzureOpenAI

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-resource.openai.azure.com")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "your-api-key")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

class MementoAIClient:
    """Interactive Memento AI Memory Client"""
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id or self.generate_user_id()
        self.azure_client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-10-21",
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        self.mcp_session = None
        self.available_tools = []
        self.conversation_history = []
        
    def generate_user_id(self) -> str:
        """Generate a unique user ID based on system info"""
        import getpass
        import platform
        
        username = getpass.getuser()
        hostname = platform.node()
        return f"{username}@{hostname}"
    
    async def connect_to_memento_server(self):
        """Connect to the Memento MCP server"""
        print("🧠 Connecting to Memento AI Memory server...")
        
        # Start the Memento server process
        import subprocess
        import sys
        
        server_process = subprocess.Popen(
            [sys.executable, "memento_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Connect to the server
        self.stdio_client = stdio_client(server_process.stdout, server_process.stdin)
        self.read, self.write = await self.stdio_client.__aenter__()
        
        self.mcp_session = ClientSession(self.read, self.write)
        await self.mcp_session.__aenter__()
        await self.mcp_session.initialize()
        
        # Get available tools
        tools_response = await self.mcp_session.list_tools()
        self.available_tools = tools_response.tools
        
        print(f"✅ Connected to Memento server with {len(self.available_tools)} tools")
        for tool in self.available_tools:
            print(f"  🔧 {tool.name}: {tool.description}")
    
    async def call_memento_tool(self, tool_name: str, arguments: dict):
        """Call a tool on the Memento MCP server"""
        try:
            # Add user_id to all tool calls
            arguments["user_id"] = self.user_id
            
            result = await self.mcp_session.call_tool(tool_name, arguments)
            return result.content[0].text
        except Exception as e:
            return f"Error calling tool {tool_name}: {str(e)}"
    
    def create_memento_tool_definitions(self):
        """Create OpenAI function definitions from Memento tools"""
        tool_definitions = []
        
        for tool in self.available_tools:
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            tool_definitions.append(tool_def)
        
        return tool_definitions
    
    async def parse_user_input(self, user_input: str) -> dict:
        """Parse user input to identify memory commands"""
        result = await self.call_memento_tool("parse_memory_command", {
            "user_input": user_input,
            "user_id": self.user_id
        })
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"intent": "unknown", "message": result}
    
    async def process_memory_command(self, user_input: str):
        """Process a memory command using Azure OpenAI and Memento tools"""
        print(f"\n💭 You: {user_input}")
        
        # First, parse the input to understand the intent
        parsed_command = await self.parse_user_input(user_input)
        
        if parsed_command["intent"] == "unknown":
            print(f"\n🤖 Memento: {parsed_command['message']}")
            return
        
        # Get tool definitions
        tools = self.create_memento_tool_definitions()
        
        # Build conversation context
        messages = [
            {
                "role": "system",
                "content": f"""You are Memento, an AI memory assistant that helps users store and recall memories using natural language.

Your catchphrase is "Hey Memento" and you help users with memory management.

User ID: {self.user_id}

Key capabilities:
1. Store memories when users say things like "Hey Memento, remember that..." or "Store this memory..."
2. Recall memories with queries like "What did I ask you to remember?" or "Show me my work memories"
3. Provide memory summaries and statistics

Available memory tools:
- store_memory: Store new memories with content, category, tags, and importance
- recall_memories: Search and retrieve stored memories based on queries
- get_memory_summary: Get statistics about stored memories
- parse_memory_command: Parse natural language to identify memory commands

When users give memory commands:
1. Use the appropriate tool to store or recall memories
2. Be conversational and friendly in your responses
3. Confirm successful storage or provide helpful recall results
4. Use the user_id to ensure data separation between users

Categories: general, work, personal, ideas, tasks
Importance scale: 1-10 (5 = normal importance)

Be helpful, conversational, and make memory management feel natural!"""
            }
        ]
        
        # Add conversation history
        messages.extend(self.conversation_history)
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Call Azure OpenAI to determine what to do
        response = self.azure_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        if message.tool_calls:
            print("🔧 Memento is processing your memory request...")
            
            # Execute tool calls
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                print(f"  📞 Using {tool_name}")
                
                # Call the Memento tool
                tool_result = await self.call_memento_tool(tool_name, tool_args)
                
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
            
            final_message = final_response.choices[0].message.content
            print(f"\n🧠 Memento: {final_message}")
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": final_message})
            
        else:
            # No tools needed, just return the response
            print(f"\n🧠 Memento: {message.content}")
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": message.content})
    
    def show_help(self):
        """Show help information"""
        print("""
🧠 **Memento: AI Memory Assistant Help**

**Catchphrase:** "Hey Memento" - Your AI memory assistant

**Memory Storage Commands:**
• "Hey Memento, remember that I have a meeting with John tomorrow"
• "Store this memory: My favorite restaurant is Luigi's Pizza"
• "I want you to remember my WiFi password is SecurePass123"
• "Don't forget that my anniversary is on March 15th"

**Memory Recall Commands:**
• "What did I ask you to remember?"
• "Show me my work-related memories"
• "What memories do you have from last week?"
• "Tell me about my personal memories"
• "What's my memory summary?"

**Categories:** general, work, personal, ideas, tasks
**Importance Scale:** 1-10 (1=low, 10=critical)

**Time-based Queries:**
• "today", "yesterday", "this week", "last week"
• "this month", "last month", "this year"

**Example Conversation:**
You: "Hey Memento, remember that my dentist appointment is next Tuesday at 2 PM"
Memento: "✅ Memory stored successfully! I've saved your dentist appointment for next Tuesday at 2 PM in your personal memories."

You: "What appointments did I ask you to remember?"
Memento: "🧠 I found your dentist appointment scheduled for next Tuesday at 2 PM..."
        """)
    
    def show_memory_stats(self):
        """Show current user's memory statistics"""
        print(f"""
📊 **Current Session Info**
👤 User ID: {self.user_id}
💬 Conversation History: {len(self.conversation_history)} messages
🔧 Available Tools: {len(self.available_tools)}
        """)
    
    async def run_interactive_session(self):
        """Run the interactive Memento session"""
        print("\n" + "="*60)
        print("🧠 Welcome to Memento: AI Memory Assistant!")
        print("="*60)
        print(f"👤 User ID: {self.user_id}")
        print("💭 Catchphrase: 'Hey Memento' - Your AI memory assistant")
        print("📝 I help you store and recall memories using natural language!")
        print("\nType 'help' for commands, 'stats' for info, or 'quit' to exit")
        print("="*60)
        
        while True:
            try:
                user_input = input("\n💭 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\n👋 Goodbye! Your memories are safely stored.")
                    break
                elif user_input.lower() == 'help':
                    self.show_help()
                elif user_input.lower() == 'stats':
                    self.show_memory_stats()
                elif user_input.lower() == 'clear':
                    self.conversation_history = []
                    print("✅ Conversation history cleared!")
                else:
                    await self.process_memory_command(user_input)
                    
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    async def cleanup(self):
        """Clean up connections"""
        if self.mcp_session:
            await self.mcp_session.__aexit__(None, None, None)
        if hasattr(self, 'stdio_client'):
            await self.stdio_client.__aexit__(None, None, None)

async def main():
    """Main function"""
    print("🚀 Memento: AI Memory System Starting...")
    
    # Check Azure OpenAI credentials
    if AZURE_OPENAI_API_KEY == "your-api-key":
        print("⚠️  Please set your Azure OpenAI credentials:")
        print("   export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com'")
        print("   export AZURE_OPENAI_API_KEY='your-api-key'")
        print("   export AZURE_OPENAI_DEPLOYMENT='your-deployment-name'")
        print("\n🎭 Running in demo mode...")
        
        # Demo conversation
        print("\n" + "="*60)
        print("🎭 DEMO: Memento AI Memory System")
        print("="*60)
        print("💭 User: Hey Memento, remember that my dog's name is Buddy and he loves tennis balls")
        print("🧠 Memento: ✅ Memory stored successfully! I've saved that your dog Buddy loves tennis balls in your personal memories.")
        print("\n💭 User: What did I tell you about my dog?")
        print("🧠 Memento: 🧠 I remember that your dog's name is Buddy and he loves tennis balls! This was stored in your personal memories.")
        print("\n💡 Set up your Azure OpenAI credentials to try the real experience!")
        return
    
    # Generate user ID
    import getpass
    import platform
    user_id = f"{getpass.getuser()}@{platform.node()}"
    
    # Initialize client
    client = MementoAIClient(user_id=user_id)
    
    try:
        # Connect to Memento server
        await client.connect_to_memento_server()
        
        # Run interactive session
        await client.run_interactive_session()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure the memento_server.py is available in the current directory")
    
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
