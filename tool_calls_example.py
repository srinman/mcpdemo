"""
This script demonstrates how Azure OpenAI's tool_calls work
by showing the actual API response structure
"""

# Example of what Azure OpenAI returns when it DOES want to use a tool
example_with_tool_calls = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": None,  # No direct text response
                "tool_calls": [   # This is what gets checked!
                    {
                        "id": "call_abc123",
                        "type": "function",
                        "function": {
                            "name": "calculate",
                            "arguments": '{"operation": "multiply", "a": 15, "b": 8}'
                        }
                    }
                ]
            }
        }
    ]
}

# Example of what Azure OpenAI returns when it DOESN'T need tools
example_without_tool_calls = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "Hello! I'm an AI assistant. How can I help you today?",
                "tool_calls": None  # No tools needed
            }
        }
    ]
}

print("🔧 When Azure OpenAI wants to use tools:")
print("message.tool_calls =", example_with_tool_calls["choices"][0]["message"]["tool_calls"])
print("✅ if message.tool_calls: → True")

print("\n💬 When Azure OpenAI responds directly:")
print("message.tool_calls =", example_without_tool_calls["choices"][0]["message"]["tool_calls"])
print("❌ if message.tool_calls: → False")
