import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

async def main():
    params = StdioServerParameters(command="python", args=["server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("🚀 MCP Client Demo - Tools, Resources, and Prompts")
            print("=" * 50)
            
            # 1. TOOL USAGE - Model-controlled (but we're calling it directly)
            print("\n1️⃣ TOOL USAGE:")
            result = await session.call_tool("greet", {"name": "Azure OpenAI"})
            print(f"   Tool Result: {result.content[0].text}")
            
            # 2. RESOURCE USAGE - App-controlled
            print("\n2️⃣ RESOURCE USAGE:")
            resource_result = await session.read_resource("info://version")
            print(f"   Resource Result: {resource_result.contents[0].text}")
            
            # 3. PROMPT USAGE - User-controlled (but we're demonstrating programmatically)
            print("\n3️⃣ PROMPT USAGE:")
            
            # First, list available prompts
            prompts = await session.list_prompts()
            print(f"   Available prompts: {len(prompts.prompts)}")
            
            for prompt in prompts.prompts:
                print(f"   - {prompt.name}: {prompt.description}")
                
                # Get the prompt content
                prompt_result = await session.get_prompt(prompt.name)
                print(f"     Prompt text: '{prompt_result.messages[0].content.text}'")
                
                # In a real UI, this prompt would be shown to the user
                # and they could use it to guide their interaction
                print(f"     💡 This prompt could guide user interaction!")
            
            print("\n✅ Demo complete! All MCP capabilities demonstrated.")


asyncio.run(main())
