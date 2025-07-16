#!/usr/bin/env python3
"""
Network traffic generator for testing the Memento network sniffer
"""

import subprocess
import sys
import time
import threading

def generate_https_traffic():
    """Generate HTTPS traffic to test the sniffer"""
    print("🔄 Generating HTTPS traffic...")
    
    urls = [
        "https://httpbin.org/ip",
        "https://api.github.com",
        "https://google.com",
        "https://microsoft.com"
    ]
    
    for url in urls:
        print(f"📡 Making request to {url}")
        try:
            subprocess.run(['curl', '-s', url], timeout=5, capture_output=True)
            time.sleep(1)
        except:
            pass

def generate_mcp_traffic():
    """Generate MCP server traffic"""
    print("🔄 Testing MCP server (port 8000)...")
    
    # Try to connect to MCP server
    try:
        subprocess.run(['curl', '-s', 'http://localhost:8000'], timeout=5, capture_output=True)
        print("📡 MCP server connection attempted")
    except:
        print("❌ MCP server not running")

def run_traffic_generation():
    """Run continuous traffic generation"""
    print("🚀 Starting traffic generation...")
    print("🔄 This will generate network traffic every 3 seconds")
    print("📡 Run the network sniffer in another terminal to see the traffic")
    print("🔄 Press Ctrl+C to stop")
    print()
    
    try:
        while True:
            generate_https_traffic()
            generate_mcp_traffic()
            print("⏱️  Waiting 3 seconds before next batch...")
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n👋 Traffic generation stopped")

if __name__ == "__main__":
    print("🚀 Network Traffic Generator")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "continuous":
        run_traffic_generation()
    else:
        print("🔄 Generating single batch of test traffic...")
        generate_https_traffic()
        generate_mcp_traffic()
        print("✅ Test traffic generated")
        print()
        print("💡 To run continuous traffic generation:")
        print("   python3 traffic_generator.py continuous")
