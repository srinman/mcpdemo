import asyncio
import os
import sys
import logging
import time
import json
from datetime import datetime
from pathlib import Path
from mcp.client.sse import sse_client
from mcp import ClientSession
from openai import AzureOpenAI
from dotenv import load_dotenv

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('memento_client_traffic.log')
    ]
)

# Create specific loggers for different components
traffic_logger = logging.getLogger('TRAFFIC')
mcp_logger = logging.getLogger('MCP')
azure_logger = logging.getLogger('AZURE')
client_logger = logging.getLogger('CLIENT')

class TrafficMonitor:
    """Network traffic monitoring for MCP and Azure OpenAI calls"""
    
    def __init__(self):
        self.request_counter = 0
        self.start_time = time.time()
        self.session_stats = {
            'azure_requests': 0,
            'mcp_requests': 0,
            'total_duration': 0
        }
    
    def log_request(self, service: str, method: str, url: str, headers: dict = None, data: dict = None):
        """Log outgoing requests"""
        self.request_counter += 1
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        traffic_logger.info(f"📤 [{self.request_counter}] {service} REQUEST at {timestamp}")
        traffic_logger.info(f"   Method: {method}")
        traffic_logger.info(f"   URL: {url}")
        
        if headers:
            traffic_logger.info(f"   Headers: {self._sanitize_headers(headers)}")
        
        if data:
            traffic_logger.info(f"   Data: {self._truncate_data(data)}")
        
        traffic_logger.info("-" * 60)
    
    def log_response(self, service: str, status_code: int = None, response_data: dict = None, duration: float = None):
        """Log incoming responses"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        traffic_logger.info(f"📥 [{self.request_counter}] {service} RESPONSE at {timestamp}")
        
        if status_code:
            traffic_logger.info(f"   Status: {status_code}")
        
        if duration:
            traffic_logger.info(f"   Duration: {duration:.3f}s")
            self.session_stats['total_duration'] += duration
        
        if response_data:
            traffic_logger.info(f"   Response: {self._truncate_data(response_data)}")
        
        traffic_logger.info("=" * 60)
        
        # Update stats
        if service == 'AZURE':
            self.session_stats['azure_requests'] += 1
        elif service == 'MCP':
            self.session_stats['mcp_requests'] += 1
    
    def log_mcp_event(self, event_type: str, details: dict = None):
        """Log MCP-specific events"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        mcp_logger.info(f"🔌 MCP {event_type} at {timestamp}")
        if details:
            mcp_logger.info(f"   Details: {details}")
    
    def log_azure_event(self, event_type: str, details: dict = None):
        """Log Azure OpenAI-specific events"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        azure_logger.info(f"🧠 AZURE {event_type} at {timestamp}")
        if details:
            azure_logger.info(f"   Details: {details}")
    
    def print_session_stats(self):
        """Print session statistics"""
        uptime = time.time() - self.start_time
        print(f"\n📊 Session Statistics:")
        print(f"   Total requests: {self.request_counter}")
        print(f"   Azure OpenAI requests: {self.session_stats['azure_requests']}")
        print(f"   MCP requests: {self.session_stats['mcp_requests']}")
        print(f"   Total response time: {self.session_stats['total_duration']:.3f}s")
        print(f"   Session uptime: {uptime:.3f}s")
    
    def _sanitize_headers(self, headers: dict) -> dict:
        """Remove sensitive information from headers"""
        sanitized = dict(headers)
        sensitive_keys = ['authorization', 'api-key', 'x-api-key', 'bearer']
        
        for key in list(sanitized.keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
        
        return sanitized
    
    def _truncate_data(self, data, max_length: int = 500) -> str:
        """Truncate data for logging"""
        if isinstance(data, dict):
            # Create a copy and sanitize sensitive data
            sanitized_data = self._sanitize_dict(data)
            data_str = json.dumps(sanitized_data, indent=2)
        else:
            data_str = str(data)
        
        if len(data_str) > max_length:
            return data_str[:max_length] + "...[TRUNCATED]"
        return data_str
    
    def _sanitize_dict(self, data: dict) -> dict:
        """Sanitize dictionary data"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_dict(item) if isinstance(item, dict) else item for item in value]
            elif any(sensitive in key.lower() for sensitive in ['api', 'key', 'token', 'secret']):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized


class TracingAzureOpenAI(AzureOpenAI):
    """Azure OpenAI client with traffic monitoring"""
    
    def __init__(self, *args, traffic_monitor: TrafficMonitor = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.traffic_monitor = traffic_monitor or TrafficMonitor()
    
    def chat_completions_create_with_tracing(self, **kwargs):
        """Chat completions with traffic monitoring"""
        start_time = time.time()
        
        # Log the request
        self.traffic_monitor.log_request(
            service="AZURE",
            method="POST",
            url=f"{self.base_url}/chat/completions",
            headers={"Authorization": "Bearer ***REDACTED***"},
            data=kwargs
        )
        
        # Log Azure event
        self.traffic_monitor.log_azure_event("CHAT_COMPLETION_REQUEST", {
            "model": kwargs.get("model"),
            "messages_count": len(kwargs.get("messages", [])),
            "tools_count": len(kwargs.get("tools", [])),
            "tool_choice": kwargs.get("tool_choice")
        })
        
        try:
            # Make the actual call
            response = self.chat.completions.create(**kwargs)
            
            # Log response
            duration = time.time() - start_time
            response_data = {
                "choices_count": len(response.choices),
                "usage": response.usage.model_dump() if response.usage else None,
                "finish_reason": response.choices[0].finish_reason if response.choices else None,
                "tool_calls": len(response.choices[0].message.tool_calls) if response.choices and response.choices[0].message.tool_calls else 0
            }
            
            self.traffic_monitor.log_response(
                service="AZURE",
                status_code=200,
                response_data=response_data,
                duration=duration
            )
            
            self.traffic_monitor.log_azure_event("CHAT_COMPLETION_RESPONSE", {
                "finish_reason": response.choices[0].finish_reason if response.choices else None,
                "tool_calls": len(response.choices[0].message.tool_calls) if response.choices and response.choices[0].message.tool_calls else 0,
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            })
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            self.traffic_monitor.log_response(
                service="AZURE",
                status_code=500,
                response_data={"error": str(e)},
                duration=duration
            )
            raise


class TracingClientSession(ClientSession):
    """MCP Client Session with traffic monitoring"""
    
    def __init__(self, *args, traffic_monitor: TrafficMonitor = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.traffic_monitor = traffic_monitor or TrafficMonitor()
    
    async def initialize_with_tracing(self):
        """Initialize with traffic monitoring"""
        start_time = time.time()
        
        self.traffic_monitor.log_mcp_event("INITIALIZATION_START")
        self.traffic_monitor.log_request(
            service="MCP",
            method="INITIALIZE",
            url="SSE Connection",
            data={"action": "initialize"}
        )
        
        try:
            result = await super().initialize()
            
            duration = time.time() - start_time
            self.traffic_monitor.log_response(
                service="MCP",
                status_code=200,
                response_data={"status": "initialized"},
                duration=duration
            )
            
            self.traffic_monitor.log_mcp_event("INITIALIZATION_SUCCESS")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.traffic_monitor.log_response(
                service="MCP",
                status_code=500,
                response_data={"error": str(e)},
                duration=duration
            )
            raise
    
    async def list_tools_with_tracing(self):
        """List tools with traffic monitoring"""
        start_time = time.time()
        
        self.traffic_monitor.log_request(
            service="MCP",
            method="LIST_TOOLS",
            url="SSE Connection",
            data={"action": "list_tools"}
        )
        
        try:
            result = await super().list_tools()
            
            duration = time.time() - start_time
            self.traffic_monitor.log_response(
                service="MCP",
                status_code=200,
                response_data={"tools_count": len(result.tools)},
                duration=duration
            )
            
            self.traffic_monitor.log_mcp_event("LIST_TOOLS_SUCCESS", {
                "tools_count": len(result.tools),
                "tool_names": [tool.name for tool in result.tools]
            })
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.traffic_monitor.log_response(
                service="MCP",
                status_code=500,
                response_data={"error": str(e)},
                duration=duration
            )
            raise
    
    async def call_tool_with_tracing(self, tool_name: str, arguments: dict):
        """Call tool with traffic monitoring"""
        start_time = time.time()
        
        self.traffic_monitor.log_request(
            service="MCP",
            method="CALL_TOOL",
            url="SSE Connection",
            data={"tool_name": tool_name, "arguments": arguments}
        )
        
        self.traffic_monitor.log_mcp_event("TOOL_CALL_START", {
            "tool_name": tool_name,
            "arguments": arguments
        })
        
        try:
            result = await super().call_tool(tool_name, arguments)
            
            duration = time.time() - start_time
            response_data = {
                "content_length": len(result.content[0].text) if result.content else 0,
                "content_type": type(result.content[0]).__name__ if result.content else None
            }
            
            self.traffic_monitor.log_response(
                service="MCP",
                status_code=200,
                response_data=response_data,
                duration=duration
            )
            
            self.traffic_monitor.log_mcp_event("TOOL_CALL_SUCCESS", {
                "tool_name": tool_name,
                "result_length": len(result.content[0].text) if result.content else 0
            })
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.traffic_monitor.log_response(
                service="MCP",
                status_code=500,
                response_data={"error": str(e)},
                duration=duration
            )
            
            self.traffic_monitor.log_mcp_event("TOOL_CALL_ERROR", {
                "tool_name": tool_name,
                "error": str(e)
            })
            
            raise


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

class TracingInteractiveMementoMCPClient:
    """Interactive client with comprehensive traffic monitoring"""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8000/sse"):
        self.mcp_server_url = mcp_server_url
        self.traffic_monitor = TrafficMonitor()
        
        # Initialize tracing Azure OpenAI client
        self.azure_client = TracingAzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-10-21",
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            traffic_monitor=self.traffic_monitor
        )
        
        self.mcp_session = None
        self.available_tools = []
        self.conversation_history = {}
        self.current_user = None
        self.users = ["alice", "bob", "charlie", "demo_user"]
        
        print("🔍 Traffic monitoring enabled - check memento_client_traffic.log for detailed logs")
    
    async def connect_to_mcp(self):
        """Connect to MCP server with tracing"""
        print("🔗 Connecting to Memento MCP server...")
        
        self.traffic_monitor.log_mcp_event("CONNECTION_START", {"url": self.mcp_server_url})
        
        self.sse_client = sse_client(self.mcp_server_url)
        self.read, self.write = await self.sse_client.__aenter__()
        
        # Create tracing MCP session
        self.mcp_session = TracingClientSession(
            self.read, 
            self.write, 
            traffic_monitor=self.traffic_monitor
        )
        
        await self.mcp_session.__aenter__()
        await self.mcp_session.initialize_with_tracing()
        
        # Get available tools with tracing
        tools_response = await self.mcp_session.list_tools_with_tracing()
        self.available_tools = tools_response.tools
        
        print(f"✅ Connected to Memento MCP server with {len(self.available_tools)} tools")
        for tool in self.available_tools:
            print(f"  🧠 {tool.name}: {tool.description}")
    
    async def call_mcp_tool(self, tool_name: str, arguments: dict):
        """Call MCP tool with tracing"""
        try:
            result = await self.mcp_session.call_tool_with_tracing(tool_name, arguments)
            return result.content[0].text
        except Exception as e:
            return f"Error calling tool {tool_name}: {str(e)}"
    
    def create_tool_definitions(self):
        """Create OpenAI function definitions from MCP tools"""
        client_logger.info("Creating tool definitions for Azure OpenAI")
        
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
            
            # Define parameters for each tool (same as original)
            if tool.name == "store_memory":
                tool_def["function"]["parameters"]["properties"].update({
                    "user_id": {"type": "string", "description": "User identifier"},
                    "content": {"type": "string", "description": "Content to store"},
                    "filename": {"type": "string", "description": "Optional filename"},
                    "description": {"type": "string", "description": "Optional description"},
                    "tags": {"type": "string", "description": "Comma-separated tags"}
                })
                tool_def["function"]["parameters"]["required"] = ["user_id", "content"]
            
            elif tool.name == "retrieve_memories":
                tool_def["function"]["parameters"]["properties"].update({
                    "user_id": {"type": "string", "description": "User identifier"},
                    "query": {"type": "string", "description": "Search query"},
                    "time_filter": {"type": "string", "description": "Time filter (today, yesterday, last_week, last_month)"},
                    "tag_filter": {"type": "string", "description": "Tag to filter by"},
                    "limit": {"type": "integer", "description": "Maximum number of results"}
                })
                tool_def["function"]["parameters"]["required"] = ["user_id"]
            
            elif tool.name == "get_memory_content":
                tool_def["function"]["parameters"]["properties"].update({
                    "user_id": {"type": "string", "description": "User identifier"},
                    "memory_id": {"type": "string", "description": "Memory ID to retrieve"}
                })
                tool_def["function"]["parameters"]["required"] = ["user_id", "memory_id"]
            
            elif tool.name == "delete_memory":
                tool_def["function"]["parameters"]["properties"].update({
                    "user_id": {"type": "string", "description": "User identifier"},
                    "memory_id": {"type": "string", "description": "Memory ID to delete"}
                })
                tool_def["function"]["parameters"]["required"] = ["user_id", "memory_id"]
            
            elif tool.name == "get_user_stats":
                tool_def["function"]["parameters"]["properties"]["user_id"] = {
                    "type": "string", "description": "User identifier"
                }
                tool_def["function"]["parameters"]["required"] = ["user_id"]
            
            elif tool.name == "list_users":
                pass  # No parameters needed
            
            tool_definitions.append(tool_def)
        
        client_logger.info(f"Created {len(tool_definitions)} tool definitions")
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
        """Chat with Azure OpenAI using tracing"""
        print(f"\n💬 You: {user_message}")
        
        client_logger.info(f"Processing user message: {user_message}")
        
        # Get tool definitions
        tools = self.create_tool_definitions()
        
        # Build conversation history for current user
        if self.current_user not in self.conversation_history:
            self.conversation_history[self.current_user] = []
        
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        messages.extend(self.conversation_history[self.current_user])
        messages.append({"role": "user", "content": user_message})
        
        # Call Azure OpenAI with tracing
        response = self.azure_client.chat_completions_create_with_tracing(
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
                
                # Auto-inject current user if not specified
                if "user_id" in tool_args and not tool_args["user_id"] and self.current_user:
                    tool_args["user_id"] = self.current_user
                elif tool_name != "list_users" and "user_id" not in tool_args and self.current_user:
                    tool_args["user_id"] = self.current_user
                
                print(f"  🔧 Calling {tool_name} with args: {tool_args}")
                
                # Call the MCP tool with tracing
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
            
            # Get final response from Azure OpenAI with tracing
            final_response = self.azure_client.chat_completions_create_with_tracing(
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
                
                client_logger.info(f"User switched from {old_user} to {self.current_user}")
                
            elif choice_num == len(self.users) + 1:
                new_user = input("Enter new user name: ").strip()
                if new_user and new_user not in self.users:
                    self.users.append(new_user)
                    self.current_user = new_user
                    print(f"✅ Added and switched to new user: {new_user}")
                    client_logger.info(f"New user added: {new_user}")
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
    
    def show_traffic_stats(self):
        """Show traffic statistics"""
        self.traffic_monitor.print_session_stats()
    
    async def run_interactive_session(self):
        """Run the interactive session with traffic monitoring"""
        print("\n🧠 Interactive Memento Memory System (WITH TRAFFIC MONITORING)")
        print("=" * 60)
        
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
            print("3. View traffic statistics")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                if not self.current_user:
                    print("Please select a user first (option 2)")
                    continue
                
                # Interactive chat
                print(f"\n💬 Chat with Memento as {self.current_user} (type 'back' to return to menu)")
                print("🔍 All network traffic is being monitored and logged")
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
                self.switch_user()
            
            elif choice == "3":
                self.show_traffic_stats()
            
            elif choice == "4":
                print("\n👋 Goodbye!")
                break
            
            else:
                print("Invalid choice. Please enter 1-4.")
    
    async def cleanup(self):
        """Clean up connections"""
        if self.mcp_session:
            await self.mcp_session.__aexit__(None, None, None)
        if hasattr(self, 'sse_client'):
            await self.sse_client.__aexit__(None, None, None)

async def main():
    """Main function with traffic monitoring"""
    print("🚀 Interactive Memento Memory System - TRAFFIC MONITORING EDITION")
    print("=" * 65)
    print("🧠 AI-powered personal memory storage")
    print("👥 Multi-user support with data isolation")
    print("🔍 Comprehensive network traffic monitoring")
    print("📋 Traffic logs saved to: memento_client_traffic.log")
    print()
    
    # Check if environment variables are set
    if AZURE_OPENAI_API_KEY == "your-api-key":
        print("⚠️  Please set your Azure OpenAI credentials in the .env file")
        return
    
    # Initialize the tracing client
    client = TracingInteractiveMementoMCPClient()
    
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
        # Show final stats
        client.show_traffic_stats()
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
