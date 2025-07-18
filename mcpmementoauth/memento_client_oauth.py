import asyncio
import os
import json
import uuid
from mcp.client.sse import sse_client
from mcp import ClientSession
from openai import AzureOpenAI
from dotenv import load_dotenv
import msal
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

# Load environment variables
load_dotenv()

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")

# Azure AD configuration
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"

# OAuth configuration
REDIRECT_URI = "http://localhost:8080/callback"
SCOPES = ["User.Read"]

class OAuthHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback"""
    def do_GET(self):
        if self.path.startswith("/callback"):
            # Parse the authorization code
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            if "code" in query_params:
                self.server.auth_code = query_params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"""
                <html>
                <body>
                    <h1>Authentication Successful!</h1>
                    <p>You can close this window and return to the application.</p>
                </body>
                </html>
                """)
            else:
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"""
                <html>
                <body>
                    <h1>Authentication Failed!</h1>
                    <p>No authorization code received.</p>
                </body>
                </html>
                """)
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress log messages
        pass

class InteractiveMementoClient:
    def __init__(self, mcp_server_url: str = "http://localhost:8000/sse"):
        self.mcp_server_url = mcp_server_url
        self.azure_client = None
        self.mcp_session = None
        self.available_tools = []
        self.conversation_history = []
        self.current_user = None
        self.access_token = None
        self.session_id = str(uuid.uuid4())
        
        # Initialize Azure OpenAI client
        if AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT:
            self.azure_client = AzureOpenAI(
                api_key=AZURE_OPENAI_API_KEY,
                api_version="2024-10-21",
                azure_endpoint=AZURE_OPENAI_ENDPOINT
            )
        
        # Initialize MSAL client
        if AZURE_CLIENT_ID and AZURE_TENANT_ID:
            self.msal_app = msal.ConfidentialClientApplication(
                AZURE_CLIENT_ID,
                authority=AZURE_AUTHORITY,
                client_credential=AZURE_CLIENT_SECRET
            )
        else:
            self.msal_app = None
    
    def authenticate_user(self):
        """Authenticate user with Azure AD"""
        if not self.msal_app:
            print("❌ Azure AD configuration not found!")
            print("   Please set AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET")
            return False
        
        try:
            print("🔐 Starting OAuth authentication...")
            
            # Start local server for callback
            server = HTTPServer(('localhost', 8080), OAuthHandler)
            server.timeout = 60
            server.auth_code = None
            
            # Start server in background
            server_thread = threading.Thread(target=server.handle_request)
            server_thread.daemon = True
            server_thread.start()
            
            # Get authorization URL
            auth_url = self.msal_app.get_authorization_request_url(
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI,
                response_type="code"
            )
            
            print(f"🌐 Opening browser for authentication...")
            print(f"   If browser doesn't open, visit: {auth_url}")
            
            # Open browser
            webbrowser.open(auth_url)
            
            # Wait for callback
            print("⏳ Waiting for authentication callback...")
            start_time = time.time()
            while server.auth_code is None and (time.time() - start_time) < 60:
                time.sleep(0.5)
            
            if server.auth_code is None:
                print("❌ Authentication timeout!")
                return False
            
            print("✅ Authorization code received!")
            
            # Exchange code for tokens
            result = self.msal_app.acquire_token_by_authorization_code(
                server.auth_code,
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
            )
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                self.current_user = result.get("id_token_claims", {}).get("name", "Unknown User")
                print(f"✅ Successfully authenticated as: {self.current_user}")
                return True
            else:
                print(f"❌ Authentication failed: {result.get('error_description', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    async def connect_to_mcp(self):
        """Connect to the MCP server and authenticate"""
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
        
        # Authenticate with MCP server
        if self.access_token:
            auth_result = await self.call_mcp_tool("authenticate", {
                "access_token": self.access_token,
                "session_id": self.session_id
            })
            print(f"🔐 MCP Authentication: {auth_result}")
        
        return True
    
    async def call_mcp_tool(self, tool_name: str, arguments: dict):
        """Call a tool on the MCP server"""
        try:
            # Add session_id to all tool calls
            if "session_id" not in arguments:
                arguments["session_id"] = self.session_id
            
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
            
            # Add parameter definitions for memento tools
            if tool.name == "store_memento":
                tool_def["function"]["parameters"]["properties"].update({
                    "content": {
                        "type": "string",
                        "description": "Content to store as memento"
                    },
                    "title": {
                        "type": "string",
                        "description": "Title for the memento"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for the memento"
                    }
                })
                tool_def["function"]["parameters"]["required"] = ["content"]
            
            elif tool.name == "retrieve_mementos":
                tool_def["function"]["parameters"]["properties"].update({
                    "query": {
                        "type": "string",
                        "description": "Search query for mementos"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days back to search"
                    }
                })
            
            elif tool.name == "store_file_memento":
                tool_def["function"]["parameters"]["properties"].update({
                    "filename": {
                        "type": "string",
                        "description": "Name of the file to store"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content of the file"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the file"
                    }
                })
                tool_def["function"]["parameters"]["required"] = ["filename", "content"]
            
            elif tool.name == "retrieve_file_memento":
                tool_def["function"]["parameters"]["properties"]["filename"] = {
                    "type": "string",
                    "description": "Name of the file to retrieve"
                }
                tool_def["function"]["parameters"]["required"] = ["filename"]
            
            tool_definitions.append(tool_def)
        
        return tool_definitions
    
    async def chat_with_azure_openai(self, user_message: str):
        """Chat with Azure OpenAI using MCP tools"""
        print(f"\n💬 You: {user_message}")
        
        if not self.azure_client:
            print("❌ Azure OpenAI not configured!")
            return
        
        # Get tool definitions
        tools = self.create_tool_definitions()
        
        # Build conversation history
        messages = [
            {
                "role": "system",
                "content": f"""You are Memento, a helpful assistant that can store and retrieve memories for users.
                You are currently talking to: {self.current_user}
                
                You have access to the following memento capabilities:
                - Store text mementos with optional titles and tags
                - Store files as mementos
                - Retrieve mementos with search queries and date filters
                - All data is user-specific and secure
                
                When users say things like:
                - "Hey memento, store this file..." → use store_file_memento
                - "Store this information..." → use store_memento
                - "What did I store last week?" → use retrieve_mementos with appropriate date filter
                - "Remember this..." → use store_memento
                - "Retrieve my notes about..." → use retrieve_mementos with query
                
                Be conversational and helpful. Always confirm what you've stored or retrieved."""
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
            print("🔧 Memento is using tools:")
            
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
            print(f"\n🧠 Memento: {final_message}")
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": final_message})
            
        else:
            # No tools needed, just return the response
            print(f"\n🧠 Memento: {message.content}")
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": message.content})
    
    def switch_user(self):
        """Switch to a different user"""
        print("\n🔄 Switching user...")
        self.current_user = None
        self.access_token = None
        self.session_id = str(uuid.uuid4())
        self.conversation_history = []
        
        if self.authenticate_user():
            print("✅ User switched successfully!")
            return True
        else:
            print("❌ User switch failed!")
            return False
    
    def show_available_tools(self):
        """Display available MCP tools"""
        print("\n🔧 Available Memento Tools:")
        for i, tool in enumerate(self.available_tools, 1):
            print(f"  {i}. {tool.name}: {tool.description}")
    
    def show_conversation_history(self):
        """Display conversation history"""
        print(f"\n📜 Conversation History for {self.current_user}:")
        if not self.conversation_history:
            print("  No conversation history yet.")
            return
        
        for i, msg in enumerate(self.conversation_history, 1):
            role = "You" if msg["role"] == "user" else "Memento"
            print(f"  {i}. {role}: {msg['content']}")
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("✅ Conversation history cleared!")
    
    async def run_interactive_session(self):
        """Run the interactive session"""
        print(f"\n🧠 Interactive Memento Chat Session")
        print("=" * 50)
        print(f"Current User: {self.current_user}")
        
        while True:
            print("\n📋 What would you like to do?")
            print("1. Chat with Memento (natural language)")
            print("2. View available tools")
            print("3. View conversation history")
            print("4. Clear conversation history")
            print("5. Switch user")
            print("6. Try example conversations")
            print("7. Exit")
            
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == "1":
                # Interactive chat
                print(f"\n💬 Chat with Memento (type 'back' to return to menu)")
                print("Try things like:")
                print("  - 'Hey memento, store this file with content: Hello World'")
                print("  - 'Remember that I like pizza'")
                print("  - 'What did I store last week?'")
                print("  - 'Store this meeting note: Met with John about project X'")
                
                while True:
                    user_input = input(f"\n{self.current_user}: ").strip()
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
                # Switch user
                if self.switch_user():
                    # Reconnect to MCP with new user
                    await self.connect_to_mcp()
            
            elif choice == "6":
                # Example conversations
                print("\n🎯 Example Conversations:")
                examples = [
                    "Hey memento, store this file called 'notes.txt' with content: Meeting notes from today",
                    "Remember that I need to call John tomorrow",
                    "Store this code snippet: print('Hello World')",
                    "What did I store yesterday?",
                    "Retrieve my files from last week",
                    "Store this shopping list: milk, bread, eggs"
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
            
            elif choice == "7":
                print(f"\n👋 Goodbye, {self.current_user}!")
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
    print("🧠 Interactive Memento MCP Client with OAuth")
    print("=" * 50)
    
    # Check configuration
    missing_config = []
    if not AZURE_OPENAI_API_KEY:
        missing_config.append("AZURE_OPENAI_API_KEY")
    if not AZURE_OPENAI_ENDPOINT:
        missing_config.append("AZURE_OPENAI_ENDPOINT")
    if not AZURE_TENANT_ID:
        missing_config.append("AZURE_TENANT_ID")
    if not AZURE_CLIENT_ID:
        missing_config.append("AZURE_CLIENT_ID")
    if not AZURE_CLIENT_SECRET:
        missing_config.append("AZURE_CLIENT_SECRET")
    
    if missing_config:
        print("⚠️  Missing configuration:")
        for config in missing_config:
            print(f"   - {config}")
        print("\nPlease check your .env file and Azure AD app registration.")
        return
    
    # Initialize the client
    client = InteractiveMementoClient()
    
    try:
        # Authenticate user
        if not client.authenticate_user():
            print("❌ Authentication failed!")
            return
        
        # Connect to MCP server
        await client.connect_to_mcp()
        
        # Run interactive session
        await client.run_interactive_session()
        
    except KeyboardInterrupt:
        print("\n\n👋 Session interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure the MCP server is running: python memento_server_oauth.py")
    
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
