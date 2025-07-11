import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

async def main():
    params = StdioServerParameters(command="python", args=["server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Call the greet tool
            result = await session.call_tool("greet", {"name": "Azure OpenAI"})
            print(result.content[0].text)


asyncio.run(main())
