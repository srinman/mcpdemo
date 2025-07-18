from mcp.server.fastmcp import FastMCP
import os
import json
import datetime

# Create the server with enhanced capabilities
mcp = FastMCP("Azure OpenAI MCP Server")

# 1. GREETING TOOL - Simple greeting with timestamp
@mcp.tool()
def greet(name: str = "world") -> str:
    """Return a personalized greeting with current timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"Hello {name}! Current time: {timestamp}"

# 2. CALCULATION TOOL - Perform mathematical operations
@mcp.tool()
def calculate(operation: str, a: float, b: float) -> str:
    """Perform mathematical operations (add, subtract, multiply, divide)"""
    try:
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                return "Error: Division by zero"
            result = a / b
        else:
            return f"Error: Unknown operation '{operation}'. Use: add, subtract, multiply, divide"
        
        return f"Result: {a} {operation} {b} = {result}"
    except Exception as e:
        return f"Error: {str(e)}"

# 3. SYSTEM INFO TOOL - Get system information
@mcp.tool()
def get_system_info() -> str:
    """Get basic system information"""
    import platform
    
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }
    
    # Try to add psutil info if available
    try:
        import psutil
        info["cpu_count"] = psutil.cpu_count()
        info["memory_gb"] = round(psutil.virtual_memory().total / (1024**3), 2)
    except ImportError:
        info["note"] = "psutil not available - install with: pip install psutil"
    
    return json.dumps(info, indent=2)

# 4. FILE OPERATIONS - Simple file operations
@mcp.tool()
def save_text_file(filename: str, content: str) -> str:
    """Save text content to a file"""
    try:
        with open(filename, 'w') as f:
            f.write(content)
        return f"Successfully saved content to {filename}"
    except Exception as e:
        return f"Error saving file: {str(e)}"

@mcp.tool()
def read_text_file(filename: str) -> str:
    """Read text content from a file"""
    try:
        with open(filename, 'r') as f:
            content = f.read()
        return f"Content of {filename}:\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

# 5. WEATHER MOCK - Mock weather service (simulated)
@mcp.tool()
def get_weather(city: str = "Seattle") -> str:
    """Get mock weather information for a city"""
    # This is a mock implementation - in real scenarios, you'd call a weather API
    import random
    
    weather_conditions = ["sunny", "cloudy", "rainy", "partly cloudy", "snowy"]
    temperature = random.randint(15, 85)  # Fahrenheit
    condition = random.choice(weather_conditions)
    
    return f"Weather in {city}: {temperature}°F, {condition}"

# RESOURCES - Information that LLMs can access
@mcp.resource("info://server-capabilities")
def server_capabilities() -> str:
    """Information about this MCP server's capabilities"""
    return """
    This MCP server provides the following capabilities:
    - Personalized greetings with timestamps
    - Mathematical calculations (add, subtract, multiply, divide)
    - System information retrieval
    - File operations (read/write text files)
    - Mock weather information
    
    This server is designed to be used by Azure OpenAI to enhance its capabilities
    with real-time data and system operations.
    """

@mcp.resource("info://usage-examples")
def usage_examples() -> str:
    """Examples of how to use this MCP server"""
    return """
    Example tool calls:
    1. greet(name="Azure OpenAI") - Get personalized greeting
    2. calculate(operation="add", a=10, b=5) - Perform math operations
    3. get_system_info() - Get system information
    4. save_text_file(filename="test.txt", content="Hello World") - Save file
    5. read_text_file(filename="test.txt") - Read file
    6. get_weather(city="San Francisco") - Get weather info
    """

# PROMPTS - Templates for user interactions
@mcp.prompt(description="Ask user what they want to calculate")
def calculation_prompt() -> str:
    return "What mathematical operation would you like me to perform? Please provide the operation (add, subtract, multiply, divide) and two numbers."

@mcp.prompt(description="Ask user for file operations")
def file_operations_prompt() -> str:
    return "What file operation would you like me to perform? I can save text to files or read existing text files."

if __name__ == "__main__":
    print("🚀 Starting Enhanced MCP Server for Azure OpenAI")
    print("📡 Server will be accessible at http://localhost:8000/sse")
    print("🔧 Available tools: greet, calculate, get_system_info, save_text_file, read_text_file, get_weather")
    print("📚 Available resources: server-capabilities, usage-examples")
    print("💡 Available prompts: calculation_prompt, file_operations_prompt")
    print()
    
    # Set environment variables for network access
    os.environ["MCP_SSE_HOST"] = "0.0.0.0"
    os.environ["MCP_SSE_PORT"] = "8000"
    
    # Run with SSE transport for network access
    mcp.run(transport="sse")
