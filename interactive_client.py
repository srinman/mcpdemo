import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

async def main():
    params = StdioServerParameters(command="python", args=["server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("🚀 Interactive MCP Client")
            print("=" * 30)
            
            while True:
                print("\n📋 What would you like to do?")
                print("1. Use a tool directly")
                print("2. Get helpful prompts") 
                print("3. Check server info")
                print("4. Exit")
                
                choice = input("\nEnter your choice (1-4): ").strip()
                
                if choice == "1":
                    # Direct tool usage
                    print("\n🔧 Available tools:")
                    tools = await session.list_tools()
                    for i, tool in enumerate(tools.tools, 1):
                        print(f"   {i}. {tool.name} - {tool.description}")
                    
                    name = input("\nEnter a name to greet: ").strip()
                    if name:
                        result = await session.call_tool("greet", {"name": name})
                        print(f"   🎉 {result.content[0].text}")
                
                elif choice == "2":
                    # PROMPT USAGE - This is the normal pattern!
                    print("\n💡 Getting helpful prompts from server...")
                    
                    # 1. Discovery: Get available prompts
                    prompts = await session.list_prompts()
                    
                    if not prompts.prompts:
                        print("   No prompts available from server.")
                        continue
                    
                    # 2. User Selection: Show prompts and let user choose
                    print(f"\n📝 Available prompts ({len(prompts.prompts)}):")
                    for i, prompt in enumerate(prompts.prompts, 1):
                        print(f"   {i}. {prompt.description}")
                    
                    try:
                        selection = int(input(f"\nSelect prompt (1-{len(prompts.prompts)}): ")) - 1
                        if 0 <= selection < len(prompts.prompts):
                            selected_prompt = prompts.prompts[selection]
                            
                            # 3. Prompt Retrieval: Get the selected prompt
                            prompt_result = await session.get_prompt(selected_prompt.name)
                            prompt_text = prompt_result.messages[0].content.text
                            
                            # 4. User Interaction: Show prompt and guide user
                            print(f"\n💭 Prompt: {prompt_text}")
                            print("   (This prompt suggests what you might want to ask)")
                            
                            # In a real UI, this would help guide the user's next input
                            user_response = input("\nYour response: ").strip()
                            if user_response:
                                # Use the response with a tool
                                result = await session.call_tool("greet", {"name": user_response})
                                print(f"   🎉 {result.content[0].text}")
                        else:
                            print("   Invalid selection.")
                    except ValueError:
                        print("   Please enter a valid number.")
                
                elif choice == "3":
                    # Resource usage
                    print("\n📚 Server Information:")
                    resource_result = await session.read_resource("info://version")
                    print(f"   Version: {resource_result.contents[0].text}")
                
                elif choice == "4":
                    print("\n👋 Goodbye!")
                    break
                
                else:
                    print("   Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    asyncio.run(main())
