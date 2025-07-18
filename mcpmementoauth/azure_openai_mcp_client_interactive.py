import asyncio
import os
from mcp.client.sse import sse_client
from mcp import ClientSession
from openai import AzureOpenAI
import json

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
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")  # Your deployment name

class InteractiveAzureOpenAIMCPClient:
    def __init__(self, mcp_server_url: str = "http://localhost:8000/sse"):
        self.mcp_server_url = mcp_server_url
        self.azure_client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-10-21",
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        self.mcp_session = None
        self.available_tools = []
        self.conversation_history = []
    
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
        for tool in self.available_tools:
            print(f"  🔧 {tool.name}: {tool.description}")
    
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
            
            # Add basic parameter definitions based on common MCP tool patterns
            if tool.name == "greet":
                tool_def["function"]["parameters"]["properties"]["name"] = {
                    "type": "string",
                    "description": "Name to greet"
                }
            elif tool.name == "calculate":
                tool_def["function"]["parameters"]["properties"].update({
                    "operation": {
                        "type": "string",
                        "description": "Mathematical operation (add, subtract, multiply, divide)"
                    },
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    }
                })
                tool_def["function"]["parameters"]["required"] = ["operation", "a", "b"]
            elif tool.name == "save_text_file":
                tool_def["function"]["parameters"]["properties"].update({
                    "filename": {
                        "type": "string",
                        "description": "Name of the file to save"
                    },
                    "content": {
                        "type": "string",
                        "description": "Text content to save"
                    }
                })
                tool_def["function"]["parameters"]["required"] = ["filename", "content"]
            elif tool.name == "read_text_file":
                tool_def["function"]["parameters"]["properties"]["filename"] = {
                    "type": "string",
                    "description": "Name of the file to read"
                }
                tool_def["function"]["parameters"]["required"] = ["filename"]
            elif tool.name == "get_weather":
                tool_def["function"]["parameters"]["properties"]["city"] = {
                    "type": "string",
                    "description": "City name for weather information"
                }
            
            tool_definitions.append(tool_def)
        
        return tool_definitions
    
    async def chat_with_azure_openai(self, user_message: str):
        """Chat with Azure OpenAI using MCP tools"""
        print(f"\n💬 You: {user_message}")
        
        # Get tool definitions
        tools = self.create_tool_definitions()
        
        # Build conversation history
        messages = [
            {
                "role": "system",
                "content": """You are a helpful assistant that can use various tools to help users. 
                You have access to MCP (Model Context Protocol) tools that can perform calculations, 
                file operations, get system information, and provide weather information.
                
                When a user asks for something that requires a tool, use the appropriate tool and 
                then provide a helpful response based on the tool's output. Be conversational and 
                friendly in your responses."""
            }
        ]
        
        # Add conversation history
        messages.extend(self.conversation_history)
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Call Azure OpenAI
        response = self.azure_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        # Process the response
        message = response.choices[0].message
        
        if message.tool_calls:
            print("🔧 Azure OpenAI is using tools:")
            
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
            
            final_message = final_response.choices[0].message.content
            print(f"\n🤖 Azure OpenAI: {final_message}")
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": final_message})
            
        else:
            # No tools needed, just return the response
            print(f"\n🤖 Azure OpenAI: {message.content}")
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": message.content})
    
    def show_available_tools(self):
        """Display available MCP tools"""
        print("\n🔧 Available MCP Tools:")
        for i, tool in enumerate(self.available_tools, 1):
            print(f"  {i}. {tool.name}: {tool.description}")
    
    def show_conversation_history(self):
        """Display conversation history"""
        print("\n📜 Conversation History:")
        if not self.conversation_history:
            print("  No conversation history yet.")
            return
        
        for i, msg in enumerate(self.conversation_history, 1):
            role = "You" if msg["role"] == "user" else "Azure OpenAI"
            print(f"  {i}. {role}: {msg['content']}")
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("✅ Conversation history cleared!")
    
    async def run_interactive_session(self):
        """Run the interactive session"""
        print("\n🤖 Interactive Azure OpenAI + MCP Chat Session")
        print("=" * 50)
        
        while True:
            print("\n📋 What would you like to do?")
            print("1. Chat with Azure OpenAI (using MCP tools)")
            print("2. View available MCP tools")
            print("3. View conversation history")
            print("4. Clear conversation history")
            print("5. Try example conversations")
            print("6. Exit")
            
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                # Interactive chat
                print("\n💬 Chat with Azure OpenAI (type 'back' to return to menu)")
                while True:
                    user_input = input("\nYou: ").strip()
                    if user_input.lower() in ['back', 'menu', 'exit']:
                        break
                    if user_input:
                        await self.chat_with_azure_openai(user_input)
            
            elif choice == "2":
                # Show available tools
                self.show_available_tools()
            
            elif choice == "3":
                # Show conversation history
                self.show_conversation_history()
            
            elif choice == "4":
                # Clear conversation history
                self.clear_conversation_history()
            
            elif choice == "5":
                # Example conversations
                print("\n🎯 Example Conversations:")
                examples = [
                    "Hello! Can you greet me and tell me what time it is?",
                    "Calculate 15 * 8 for me",
                    "What's the weather like in San Francisco?",
                    "Save a message 'Hello from Azure OpenAI + MCP!' to a file called 'demo.txt'",
                    "Now read that file back to me",
                    "Can you get system information about this computer?"
                ]
                
                for i, example in enumerate(examples, 1):
                    print(f"  {i}. {example}")
                
                try:
                    selection = int(input(f"\nSelect example (1-{len(examples)}, 0 to cancel): "))
                    if 1 <= selection <= len(examples):
                        await self.chat_with_azure_openai(examples[selection - 1])
                    elif selection == 0:
                        continue
                    else:
                        print("Invalid selection.")
                except ValueError:
                    print("Please enter a valid number.")
            
            elif choice == "6":
                print("\n👋 Goodbye!")
                break
            
            else:
                print("Invalid choice. Please enter 1-6.")
    
    async def cleanup(self):
        """Clean up connections"""
        if self.mcp_session:
            await self.mcp_session.__aexit__(None, None, None)
        if hasattr(self, 'sse_client'):
            await self.sse_client.__aexit__(None, None, None)

async def main():
    """Main function"""
    print("🚀 Interactive Azure OpenAI + MCP Integration")
    print("=" * 50)
    
    # Check if environment variables are set
    if AZURE_OPENAI_API_KEY == "your-api-key":
        print("⚠️  Please set your Azure OpenAI credentials:")
        print("   export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com'")
        print("   export AZURE_OPENAI_API_KEY='your-api-key'")
        print("   export AZURE_OPENAI_DEPLOYMENT='your-deployment-name'")
        print("\n📝 For this demo, I'll show you what the interaction would look like...")
        
        # Demo mode - show what would happen
        print("\n🎭 DEMO MODE - Simulated Azure OpenAI + MCP interaction:")
        print("💬 User: Calculate 15 + 25 and then save the result to a file")
        print("🔧 Azure OpenAI would call: calculate(operation='add', a=15, b=25)")
        print("📋 MCP Result: Result: 15.0 add 25.0 = 40.0")
        print("🔧 Azure OpenAI would call: save_text_file(filename='calculation.txt', content='15 + 25 = 40')")
        print("📋 MCP Result: Successfully saved content to calculation.txt")
        print("🤖 Azure OpenAI: I've calculated 15 + 25 = 40 and saved the result to calculation.txt")
        print("\n💡 Set up your credentials to try the real interactive experience!")
        return
    
    # Initialize the client
    client = InteractiveAzureOpenAIMCPClient()
    
    try:
        # Connect to MCP server
        await client.connect_to_mcp()
        
        # Run interactive session
        await client.run_interactive_session()
        
    except KeyboardInterrupt:
        print("\n\n👋 Session interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure the MCP server is running: python azure_mcp_server.py")
    
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
