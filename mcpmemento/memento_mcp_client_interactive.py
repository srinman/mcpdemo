import asyncio
import os
import sys
from pathlib import Path
from mcp.client.sse import sse_client
from mcp import ClientSession
from openai import AzureOpenAI
import json
from dotenv import load_dotenv

# Load environment variables from parent directory
parent_dir = Path(__file__).parent.parent
env_path = parent_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env file from {env_path}")
else:
    print("⚠️  .env file not found in parent directory")

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-resource.openai.azure.com")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "your-api-key")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

class InteractiveMementoMCPClient:
    def __init__(self, mcp_server_url: str = "http://4.153.91.177:8000/sse"):
        self.mcp_server_url = mcp_server_url
        self.azure_client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-10-21",
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        self.mcp_session = None
        self.available_tools = []
        self.conversation_history = {}  # Per-user conversation history
        self.current_user = None
        self.users = ["alice", "bob", "charlie", "demo_user"]  # Default users
    
    async def connect_to_mcp(self):
        """Connect to the MCP server and get available tools"""
        print("🔗 Connecting to Memento MCP server...")
        self.sse_client = sse_client(self.mcp_server_url)
        self.read, self.write = await self.sse_client.__aenter__()
        
        self.mcp_session = ClientSession(self.read, self.write)
        await self.mcp_session.__aenter__()
        await self.mcp_session.initialize()
        
        # Get available tools
        tools_response = await self.mcp_session.list_tools()
        self.available_tools = tools_response.tools
        
        print(f"✅ Connected to Memento MCP server with {len(self.available_tools)} tools")
        for tool in self.available_tools:
            print(f"  🧠 {tool.name}: {tool.description}")
    
    async def call_mcp_tool(self, tool_name: str, arguments: dict):
        """Call a tool on the MCP server"""
        try:
            result = await self.mcp_session.call_tool(tool_name, arguments)
            return result.content[0].text
        except Exception as e:
            return f"Error calling tool {tool_name}: {str(e)}"
    
    def create_tool_definitions(self):
        """Create OpenAI function definitions from MCP tools"""
        tool_definitions = []
        
        for tool in self.available_tools:
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
            
            # Define parameters for each tool
            if tool.name == "store_memory":
                tool_def["function"]["parameters"]["properties"].update({
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to store"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional filename"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description"
                    },
                    "tags": {
                        "type": "string",
                        "description": "Comma-separated tags"
                    }
                })
                tool_def["function"]["parameters"]["required"] = ["user_id", "content"]
            
            elif tool.name == "retrieve_memories":
                tool_def["function"]["parameters"]["properties"].update({
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "time_filter": {
                        "type": "string",
                        "description": "Time filter (today, yesterday, last_week, last_month)"
                    },
                    "tag_filter": {
                        "type": "string",
                        "description": "Tag to filter by"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results"
                    }
                })
                tool_def["function"]["parameters"]["required"] = ["user_id"]
            
            elif tool.name == "get_memory_content":
                tool_def["function"]["parameters"]["properties"].update({
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "memory_id": {
                        "type": "string",
                        "description": "Memory ID to retrieve"
                    }
                })
                tool_def["function"]["parameters"]["required"] = ["user_id", "memory_id"]
            
            elif tool.name == "delete_memory":
                tool_def["function"]["parameters"]["properties"].update({
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "memory_id": {
                        "type": "string",
                        "description": "Memory ID to delete"
                    }
                })
                tool_def["function"]["parameters"]["required"] = ["user_id", "memory_id"]
            
            elif tool.name == "get_user_stats":
                tool_def["function"]["parameters"]["properties"]["user_id"] = {
                    "type": "string",
                    "description": "User identifier"
                }
                tool_def["function"]["parameters"]["required"] = ["user_id"]
            
            elif tool.name == "list_users":
                # No parameters needed
                pass
            
            tool_definitions.append(tool_def)
        
        return tool_definitions
    
    def get_system_prompt(self):
        """Get system prompt with current user context"""
        current_user_info = f"Current user: {self.current_user}" if self.current_user else "No user selected"
        
        return f"""You are Memento, a helpful AI assistant that manages personal memory storage for users.
You can help users store, retrieve, and manage their personal memories (text content, notes, files, etc.).

{current_user_info}

Key capabilities:
- Store memories for specific users with descriptions and tags
- Retrieve memories using natural language queries
- Search by content, time periods, and tags
- Manage user data with complete isolation between users
- Provide statistics and user management features

When users mention "store this", "remember this", "save this", etc., use the store_memory tool.
When users ask "what did I store", "find my notes", "retrieve memories", etc., use retrieve_memories.
Always include the user_id parameter when calling tools that require it.

If no user is currently selected and a user-specific operation is requested, ask them to select a user first.

Be conversational and helpful. Interpret natural language requests and translate them into appropriate tool calls.
"""
    
    async def chat_with_azure_openai(self, user_message: str):
        """Chat with Azure OpenAI using Memento MCP tools"""
        print(f"\n💬 You: {user_message}")
        
        # Get tool definitions
        tools = self.create_tool_definitions()
        
        # Build conversation history for current user
        if self.current_user not in self.conversation_history:
            self.conversation_history[self.current_user] = []
        
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        messages.extend(self.conversation_history[self.current_user])
        messages.append({"role": "user", "content": user_message})
        
        # Call Azure OpenAI
        response = self.azure_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        if message.tool_calls:
            print("🧠 Memento is using tools:")
            
            # Execute tool calls
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                # Auto-inject current user if not specified and tool requires user_id
                if "user_id" in tool_args and not tool_args["user_id"] and self.current_user:
                    tool_args["user_id"] = self.current_user
                elif tool_name != "list_users" and "user_id" not in tool_args and self.current_user:
                    tool_args["user_id"] = self.current_user
                
                print(f"  🔧 Calling {tool_name} with args: {tool_args}")
                
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
            
            final_message = final_response.choices[0].message.content
            print(f"\n🧠 Memento: {final_message}")
            
            # Update conversation history
            self.conversation_history[self.current_user].append({"role": "user", "content": user_message})
            self.conversation_history[self.current_user].append({"role": "assistant", "content": final_message})
            
        else:
            # No tools needed, just return the response
            print(f"\n🧠 Memento: {message.content}")
            
            # Update conversation history
            self.conversation_history[self.current_user].append({"role": "user", "content": user_message})
            self.conversation_history[self.current_user].append({"role": "assistant", "content": message.content})
    
    def switch_user(self):
        """Switch to a different user"""
        print("\n👥 User Management")
        print("=" * 30)
        
        print("Current available users:")
        for i, user in enumerate(self.users, 1):
            current_indicator = " (current)" if user == self.current_user else ""
            print(f"  {i}. {user}{current_indicator}")
        
        print(f"  {len(self.users) + 1}. Add new user")
        print(f"  {len(self.users) + 2}. Back to main menu")
        
        try:
            choice = input(f"\nSelect user (1-{len(self.users) + 2}): ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(self.users):
                old_user = self.current_user
                self.current_user = self.users[choice_num - 1]
                print(f"✅ Switched to user: {self.current_user}")
                if old_user != self.current_user:
                    print(f"   Previous user: {old_user}")
                
            elif choice_num == len(self.users) + 1:
                new_user = input("Enter new user name: ").strip()
                if new_user and new_user not in self.users:
                    self.users.append(new_user)
                    self.current_user = new_user
                    print(f"✅ Added and switched to new user: {new_user}")
                elif new_user in self.users:
                    print(f"User {new_user} already exists")
                else:
                    print("Invalid user name")
            
            elif choice_num == len(self.users) + 2:
                return
            
            else:
                print("Invalid choice")
                
        except ValueError:
            print("Please enter a valid number")
    
    def show_available_tools(self):
        """Display available MCP tools"""
        print("\n🔧 Available Memento Tools:")
        for i, tool in enumerate(self.available_tools, 1):
            print(f"  {i}. {tool.name}: {tool.description}")
    
    def show_conversation_history(self):
        """Display conversation history for current user"""
        if not self.current_user:
            print("No user selected")
            return
        
        print(f"\n📜 Conversation History for {self.current_user}:")
        
        if self.current_user not in self.conversation_history or not self.conversation_history[self.current_user]:
            print("  No conversation history yet.")
            return
        
        for i, msg in enumerate(self.conversation_history[self.current_user], 1):
            role = "You" if msg["role"] == "user" else "Memento"
            print(f"  {i}. {role}: {msg['content']}")
    
    def clear_conversation_history(self):
        """Clear conversation history for current user"""
        if not self.current_user:
            print("No user selected")
            return
        
        if self.current_user in self.conversation_history:
            self.conversation_history[self.current_user] = []
        print(f"✅ Conversation history cleared for {self.current_user}!")
    
    async def run_example_commands(self):
        """Run example commands to demonstrate functionality"""
        if not self.current_user:
            print("Please select a user first")
            return
        
        print(f"\n🎯 Example Commands for {self.current_user}:")
        examples = [
            f"Hey memento, store this meeting summary: 'Discussed Q4 planning and budget allocation' with tags 'work,meeting'",
            f"Save this recipe: 'Chocolate chip cookies: 2 cups flour, 1 cup butter...' for later",
            f"Remember this quote: 'The best time to plant a tree was 20 years ago. The second best time is now.'",
            f"What memories do I have from last week?",
            f"Find all my work-related notes",
            f"Show me my storage statistics",
            f"List all stored memories"
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"  {i}. {example}")
        
        try:
            selection = int(input(f"\nSelect example (1-{len(examples)}, 0 to cancel): "))
            if 1 <= selection <= len(examples):
                await self.chat_with_azure_openai(examples[selection - 1])
            elif selection == 0:
                return
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a valid number.")
    
    async def run_interactive_session(self):
        """Run the interactive session"""
        print("\n🧠 Interactive Memento Memory System")
        print("=" * 40)
        
        # Initial user selection
        if not self.current_user:
            print("Welcome! Please select a user to get started.")
            self.switch_user()
        
        while True:
            current_user_display = f"Current user: {self.current_user}" if self.current_user else "No user selected"
            print(f"\n📋 Memento Main Menu ({current_user_display})")
            print("=" * 50)
            print("1. Chat with Memento (natural language memory operations)")
            print("2. Switch user")
            print("3. View available tools")
            print("4. View conversation history")
            print("5. Clear conversation history")
            print("6. Try example commands")
            print("7. Exit")
            
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == "1":
                if not self.current_user:
                    print("Please select a user first (option 2)")
                    continue
                
                # Interactive chat
                print(f"\n💬 Chat with Memento as {self.current_user} (type 'back' to return to menu)")
                print("Examples:")
                print("- 'Hey memento, store this file content...'")
                print("- 'What did I store last week?'")
                print("- 'Find my notes about meetings'")
                print("- 'Show me my storage stats'")
                
                while True:
                    user_input = input(f"\n{self.current_user}: ").strip()
                    if user_input.lower() in ['back', 'menu', 'exit']:
                        break
                    if user_input:
                        await self.chat_with_azure_openai(user_input)
            
            elif choice == "2":
                # Switch user
                self.switch_user()
            
            elif choice == "3":
                # Show available tools
                self.show_available_tools()
            
            elif choice == "4":
                # Show conversation history
                self.show_conversation_history()
            
            elif choice == "5":
                # Clear conversation history
                self.clear_conversation_history()
            
            elif choice == "6":
                # Example commands
                await self.run_example_commands()
            
            elif choice == "7":
                print("\n👋 Goodbye!")
                break
            
            else:
                print("Invalid choice. Please enter 1-7.")
    
    async def cleanup(self):
        """Clean up connections"""
        if self.mcp_session:
            await self.mcp_session.__aexit__(None, None, None)
        if hasattr(self, 'sse_client'):
            await self.sse_client.__aexit__(None, None, None)

async def main():
    """Main function"""
    print("🚀 Interactive Memento Memory System")
    print("=" * 40)
    print("🧠 AI-powered personal memory storage")
    print("👥 Multi-user support with data isolation")
    print("🔍 Natural language memory operations")
    print()
    
    # Check if environment variables are set
    if AZURE_OPENAI_API_KEY == "your-api-key":
        print("⚠️  Please set your Azure OpenAI credentials in the .env file:")
        print("   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com")
        print("   AZURE_OPENAI_API_KEY=your-api-key")
        print("   AZURE_OPENAI_DEPLOYMENT=your-deployment-name")
        print()
        
        demo_mode = input("Would you like to see a demo of the system? (y/n): ").lower().strip()
        
        if demo_mode.startswith('y'):
            print("\n🎭 DEMO MODE - Simulated Memento interactions:")
            print("💬 User (alice): Hey memento, store this meeting summary about Q4 planning")
            print("🔧 Memento would call: store_memory(user_id='alice', content='Meeting summary...', tags='work,meeting')")
            print("📋 MCP Result: Successfully stored 'meeting_summary.txt' for user alice")
            print("🧠 Memento: I've stored your meeting summary! It's tagged with 'work' and 'meeting' for easy retrieval.")
            print()
            print("💬 User (alice): What did I store last week?")
            print("🔧 Memento would call: retrieve_memories(user_id='alice', time_filter='last_week')")
            print("📋 MCP Result: Found 3 memories for user alice from last week...")
            print("🧠 Memento: I found 3 memories from last week: meeting summary, project notes, and a recipe!")
            print()
            print("💡 Set up your credentials to try the real interactive experience!")
        
        return
    
    # Initialize the client
    client = InteractiveMementoMCPClient()
    
    try:
        # Connect to MCP server
        await client.connect_to_mcp()
        
        # Run interactive session
        await client.run_interactive_session()
        
    except KeyboardInterrupt:
        print("\n\n👋 Session interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure the Memento MCP server is running:")
        print("  python memento_mcp_server.py")
    
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
