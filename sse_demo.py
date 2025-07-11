#!/usr/bin/env python3
"""
HTTP-level demonstration of SSE communication
This shows what happens at the raw HTTP level when using SSE
"""

import asyncio
import aiohttp
import json

async def demonstrate_sse_communication():
    """Demonstrate raw SSE communication with MCP server"""
    
    print("🔍 Demonstrating SSE communication at HTTP level...")
    
    # Connect to the SSE endpoint
    async with aiohttp.ClientSession() as session:
        print("📡 Opening SSE connection to http://localhost:8000/sse")
        
        # This is what sse_client does internally
        async with session.get(
            'http://localhost:8000/sse',
            headers={
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache'
            }
        ) as response:
            print(f"✅ HTTP Response Status: {response.status}")
            print(f"📋 Content-Type: {response.headers.get('Content-Type')}")
            print(f"🔄 Connection: {response.headers.get('Connection')}")
            print()
            
            # Read SSE events
            print("📨 Reading SSE events...")
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    # Extract JSON data from SSE event
                    data = line[6:]  # Remove 'data: ' prefix
                    try:
                        message = json.loads(data)
                        print(f"🔔 Received SSE event: {json.dumps(message, indent=2)}")
                    except json.JSONDecodeError:
                        print(f"📝 Raw SSE data: {data}")
                elif line:
                    print(f"📄 SSE line: {line}")

if __name__ == "__main__":
    print("⚠️  Make sure the MCP server is running first!")
    print("   Run: python servernetwork.py")
    print()
    
    try:
        asyncio.run(demonstrate_sse_communication())
    except KeyboardInterrupt:
        print("\n👋 Demonstration stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Make sure the server is running on http://localhost:8000")
