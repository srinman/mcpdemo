#!/usr/bin/env python3
"""
Memento: AI Memory Client (File-Based Storage)

Interactive client for the Memento AI Memory system using file-based storage.
Integrates with Azure OpenAI for natural language processing and the file-based
Memento MCP server for memory management.

Features:
- Natural language memory commands
- Azure OpenAI integration for conversational interface
- File-based memory storage with user separation
- Interactive chat interface
- Memory statistics and exploration
"""

import asyncio
import json
import os
import getpass
import platform
from datetime import datetime
from typing import Dict, List, Optional

# Azure OpenAI imports
from openai import AzureOpenAI

# MCP imports
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client


# Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")


class MementoFileClient:
    """Interactive Memento client using file-based storage."""
    
    def __init__(self):
        self.azure_client = None
        self.mcp_session = None
        self.conversation_history = []
        self.user_id = self.generate_user_id()
        
    def generate_user_id(self) -> str:
        """Generate a unique user ID based on system info."""
        username = getpass.getuser()
        hostname = platform.node()
        return f"{username}@{hostname}"
    
    async def initialize(self):
        """Initialize both Azure OpenAI and MCP connections."""
        # Initialize Azure OpenAI
        if AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY:
            self.azure_client = AzureOpenAI(
                api_key=AZURE_OPENAI_API_KEY,
                api_version="2024-02-01",
                azure_endpoint=AZURE_OPENAI_ENDPOINT
            )
            print("✅ Azure OpenAI client initialized")
        else:
            print("⚠️ Azure OpenAI credentials not found - running in basic mode")
        
        # Initialize MCP session
        await self.connect_to_mcp()
        
        print(f"👤 User ID: {self.user_id}")
        print("🎉 Memento File-Based Memory System Ready!")
    
    async def connect_to_mcp(self):
        """Connect to the Memento MCP server."""
        try:
            # Start the MCP server as a subprocess
            import subprocess
            server_process = subprocess.Popen(
                ["python", "memento_server_files.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Create MCP session
            session = await stdio_client(server_process.stdin, server_process.stdout).__aenter__()
            self.mcp_session = session
            
            print("✅ Connected to Memento MCP Server (file-based)")
            
        except Exception as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            raise
    
    async def get_mcp_tools_schema(self):
        """Get available tools from MCP server in Azure OpenAI format."""
        try:
            # List tools
            result = await self.mcp_session.list_tools()
            tools_list = result.tools
            
            # Convert MCP tools to Azure OpenAI function format
            azure_tools = []
            for tool in tools_list:
                azure_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                }
                azure_tools.append(azure_tool)
            
            return azure_tools
            
        except Exception as e:
            print(f"❌ Error getting MCP tools: {e}")
            return []
    
    async def call_mcp_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute MCP tool and return result."""
        try:
            # Always add user_id to arguments for proper file access control
            if "user_id" not in arguments:
                arguments["user_id"] = self.user_id
            
            # Call the tool
            result = await self.mcp_session.call_tool(tool_name, arguments)
            
            # Extract result safely
            if result.content and len(result.content) > 0:
                return result.content[0].text
            else:
                return "Tool executed successfully but returned no result"
                
        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"
    
    async def process_with_azure_openai(self, user_message: str):
        """Process user message with Azure OpenAI and MCP tools."""
        if not self.azure_client:
            # Fallback mode without Azure OpenAI
            await self.process_without_azure_openai(user_message)
            return
        
        # Build message history
        messages = [
            {
                "role": "system",
                "content": """You are Memento, an AI memory assistant. You help users store and recall memories using natural language commands.

Key capabilities:
- Store memories with "Hey Memento, remember..." or "Store this memory..."
- Recall memories with "What did I store..." or "Show me memories about..."
- Support time-based queries like "last week", "this month"
- Support category filtering like "work memories", "personal notes"
- Provide memory summaries and statistics

You use file-based storage where each user has their own separate JSON file for complete data isolation.

Always be helpful, conversational, and make memory management feel natural."""
            }
        ]
        
        # Add conversation history
        messages.extend(self.conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            # Get available tools from MCP
            tools = await self.get_mcp_tools_schema()
            
            if not tools:
                print("⚠️ No MCP tools available")
                return
            
            # PHASE 1: Azure OpenAI plans tool usage
            response = self.azure_client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # PHASE 2: Execute tools if requested
            if message.tool_calls:
                print("🔧 Using memory tools:")
                
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    print(f"  📁 {tool_name}({list(tool_args.keys())})")
                    
                    # Execute MCP tool
                    tool_result = await self.call_mcp_tool(tool_name, tool_args)
                    
                    # Add tool call and result to message history
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call.model_dump()]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                
                # PHASE 3: Get final response from Azure OpenAI
                final_response = self.azure_client.chat.completions.create(
                    model=AZURE_OPENAI_DEPLOYMENT,
                    messages=messages
                )
                
                final_message = final_response.choices[0].message.content
                print(f"\n🧠 Memento: {final_message}")
                
                # Update conversation history
                self.conversation_history.append({"role": "user", "content": user_message})
                self.conversation_history.append({"role": "assistant", "content": final_message})
                
            else:
                # No tools needed - direct response
                response_content = message.content
                print(f"\n🧠 Memento: {response_content}")
                
                # Update conversation history
                self.conversation_history.append({"role": "user", "content": user_message})
                self.conversation_history.append({"role": "assistant", "content": response_content})
                
        except Exception as e:
            print(f"\n❌ Error processing with Azure OpenAI: {e}")
    
    async def process_without_azure_openai(self, user_message: str):
        """Fallback processing without Azure OpenAI (direct tool calls)."""
        user_lower = user_message.lower()
        
        # Simple pattern matching for basic functionality
        if any(trigger in user_lower for trigger in ["remember", "store", "hey memento"]):
            # Storage command
            result = await self.call_mcp_tool("store_memory", {
                "text": user_message
            })
            print(f"\n📁 Memory stored: {result}")
            
        elif any(trigger in user_lower for trigger in ["recall", "what", "show", "find"]):
            # Recall command
            result = await self.call_mcp_tool("recall_memories", {
                "query": user_message
            })
            print(f"\n🔍 Memory search results: {result}")
            
        elif "summary" in user_lower:
            # Summary command
            result = await self.call_mcp_tool("get_memory_summary", {})
            print(f"\n📊 Memory summary: {result}")
            
        else:
            print("\n🤔 I'm not sure what you want to do. Try:")
            print("  - 'Remember that...' to store a memory")
            print("  - 'What did I store about...' to recall memories")
            print("  - 'Show me a summary' to see memory statistics")
    
    def display_main_menu(self):
        """Display the main menu options."""
        print("\n" + "="*60)
        print("🧠 Memento: AI Memory (File-Based Storage)")
        print("="*60)
        print("📋 What would you like to do?")
        print("1. 💬 Chat with Memento (store and recall memories)")
        print("2. 🔧 View available memory tools")
        print("3. 📜 View conversation history")
        print("4. 🗑️  Clear conversation history")
        print("5. 📊 Show memory summary")
        print("6. 👥 List all memory users (debug)")
        print("7. 🚪 Exit")
        print("="*60)
    
    async def chat_session(self):
        """Interactive chat session with Memento."""
        print("\n🎉 Starting chat with Memento!")
        print("💡 You can use natural language to store and recall memories.")
        print("📁 Each user gets their own secure memory file.")
        print("💬 Type 'back' to return to main menu\n")
        
        while True:
            try:
                user_input = input(f"\n👤 You: ").strip()
                
                if user_input.lower() == 'back':
                    print("🔙 Returning to main menu...")
                    break
                    
                if not user_input:
                    print("⚠️ Please enter a message.")
                    continue
                    
                # Process user input
                await self.process_with_azure_openai(user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat session ended.")
                break
            except Exception as e:
                print(f"\n❌ Error in chat session: {e}")
    
    async def show_available_tools(self):
        """Display available MCP tools."""
        try:
            result = await self.mcp_session.list_tools()
            tools = result.tools
            
            print("\n🔧 Available Memory Tools:")
            print("-" * 40)
            for i, tool in enumerate(tools, 1):
                print(f"{i}. {tool.name}")
                print(f"   📝 {tool.description}")
                print()
                
        except Exception as e:
            print(f"❌ Error getting tools: {e}")
    
    def show_conversation_history(self):
        """Display conversation history."""
        if not self.conversation_history:
            print("\n📜 No conversation history yet.")
            return
            
        print("\n📜 Conversation History:")
        print("-" * 40)
        for i, msg in enumerate(self.conversation_history, 1):
            role_icon = "👤" if msg["role"] == "user" else "🧠"
            print(f"{i}. {role_icon} {msg['role'].title()}: {msg['content'][:100]}...")
        print()
    
    def clear_conversation_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()
        print("\n🗑️ Conversation history cleared.")
    
    async def show_memory_summary(self):
        """Show memory summary for current user."""
        try:
            result = await self.call_mcp_tool("get_memory_summary", {})
            print(f"\n📊 Memory Summary:")
            print("-" * 40)
            print(result)
            
        except Exception as e:
            print(f"❌ Error getting memory summary: {e}")
    
    async def list_all_users(self):
        """List all users (debug function)."""
        try:
            result = await self.call_mcp_tool("list_memory_users", {})
            print(f"\n👥 All Memory Users:")
            print("-" * 40)
            print(result)
            
        except Exception as e:
            print(f"❌ Error listing users: {e}")
    
    async def run_interactive_session(self):
        """Main interactive session loop."""
        while True:
            try:
                self.display_main_menu()
                
                choice = input("\nEnter your choice (1-7): ").strip()
                
                if choice == "1":
                    await self.chat_session()
                elif choice == "2":
                    await self.show_available_tools()
                elif choice == "3":
                    self.show_conversation_history()
                elif choice == "4":
                    self.clear_conversation_history()
                elif choice == "5":
                    await self.show_memory_summary()
                elif choice == "6":
                    await self.list_all_users()
                elif choice == "7":
                    print("\n👋 Goodbye! Your memories are safely stored in files.")
                    break
                else:
                    print("\n❌ Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    async def cleanup(self):
        """Clean up resources."""
        if self.mcp_session:
            try:
                await self.mcp_session.__aexit__(None, None, None)
            except:
                pass


async def main():
    """Main entry point."""
    print("🧠 Memento: AI Memory System (File-Based Storage)")
    print("=" * 50)
    
    client = MementoFileClient()
    
    try:
        await client.initialize()
        await client.run_interactive_session()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
