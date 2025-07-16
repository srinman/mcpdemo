#!/usr/bin/env python3
"""
Simple network capture test to verify tcpdump is working
"""

import subprocess
import sys
import time
import threading

def test_basic_capture():
    """Test basic network capture"""
    print("🔍 Testing basic network capture...")
    print("📡 This will capture ANY network traffic for 10 seconds")
    print("🔄 Try browsing a website or running a network command in another terminal")
    print()
    
    # Very basic tcpdump command
    cmd = ['sudo', 'tcpdump', '-i', 'any', '-n', '-c', '10', '-v']
    
    print(f"Running: {' '.join(cmd)}")
    print("=" * 50)
    
    try:
        result = subprocess.run(cmd, timeout=15, capture_output=True, text=True)
        
        if result.stdout:
            print("✅ SUCCESS: Network capture is working!")
            print("\nCaptured traffic:")
            print("-" * 30)
            print(result.stdout)
        else:
            print("❌ No traffic captured")
            if result.stderr:
                print(f"Error: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        print("⏱️  Timeout - no traffic captured in 15 seconds")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_port_specific():
    """Test port-specific capture"""
    print("\n🔍 Testing port-specific capture (port 443 - HTTPS)")
    print("📡 This will capture HTTPS traffic for 10 seconds")
    print("🔄 Try visiting https://google.com in another terminal: curl https://google.com")
    print()
    
    # Port 443 specific
    cmd = ['sudo', 'tcpdump', '-i', 'any', '-n', '-c', '5', 'port', '443']
    
    print(f"Running: {' '.join(cmd)}")
    print("=" * 50)
    
    try:
        result = subprocess.run(cmd, timeout=15, capture_output=True, text=True)
        
        if result.stdout:
            print("✅ SUCCESS: Port 443 capture is working!")
            print("\nCaptured HTTPS traffic:")
            print("-" * 30)
            print(result.stdout)
        else:
            print("❌ No HTTPS traffic captured")
            if result.stderr:
                print(f"Error: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        print("⏱️  Timeout - no HTTPS traffic captured in 15 seconds")
    except Exception as e:
        print(f"❌ Error: {e}")

def generate_test_traffic():
    """Generate some test traffic"""
    print("\n🔄 Generating test traffic...")
    
    def make_request():
        try:
            import requests
            response = requests.get('https://httpbin.org/ip', timeout=5)
            print(f"✅ Test request successful: {response.status_code}")
        except Exception as e:
            print(f"❌ Test request failed: {e}")
    
    # Make request in background
    thread = threading.Thread(target=make_request)
    thread.start()
    thread.join(timeout=10)

if __name__ == "__main__":
    print("🚀 Network Capture Test")
    print("=" * 40)
    
    # Test 1: Basic capture
    test_basic_capture()
    
    # Test 2: Generate traffic and test
    generate_test_traffic()
    
    # Test 3: Port-specific capture
    test_port_specific()
    
    print("\n🏁 Network capture test completed")
    print("💡 If no traffic was captured, try:")
    print("   1. Running: sudo tcpdump -i any -n -c 5")
    print("   2. In another terminal: curl https://google.com")
    print("   3. Check if tcpdump has proper permissions")
