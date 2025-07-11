import asyncio
import os
from mcp.client.sse import sse_client
from mcp import ClientSession
from openai import AzureOpenAI
import json

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-resource.openai.azure.com")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "your-api-key")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")  # Your deployment name

class AzureOpenAIMCPClient:
    def __init__(self, mcp_server_url: str = "http://localhost:8000/sse"):
        self.mcp_server_url = mcp_server_url
        self.azure_client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-10-21",
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        self.mcp_session = None
        self.available_tools = []
    
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
    
    async def chat_with_tools(self, user_message: str):
        """Chat with Azure OpenAI using MCP tools"""
        print(f"\n💬 User: {user_message}")
        
        # Get tool definitions
        tools = self.create_tool_definitions()
        
        # Create initial message
        messages = [
            {
                "role": "system",
                "content": """You are a helpful assistant that can use various tools to help users. 
                You have access to MCP (Model Context Protocol) tools that can perform calculations, 
                file operations, get system information, and provide weather information.
                
                When a user asks for something that requires a tool, use the appropriate tool and 
                then provide a helpful response based on the tool's output."""
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
        
        # Process the response
        message = response.choices[0].message
        
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
            
            final_message = final_response.choices[0].message.content
            print(f"🤖 Azure OpenAI: {final_message}")
            
        else:
            # No tools needed, just return the response
            print(f"🤖 Azure OpenAI: {message.content}")
    
    async def cleanup(self):
        """Clean up connections"""
        if self.mcp_session:
            await self.mcp_session.__aexit__(None, None, None)
        if hasattr(self, 'sse_client'):
            await self.sse_client.__aexit__(None, None, None)

async def main():
    """Main demo function"""
    print("🚀 Azure OpenAI + MCP Integration Demo")
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
            await asyncio.sleep(1)  # Small delay between requests
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the MCP server is running: python azure_mcp_server.py")
    
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
