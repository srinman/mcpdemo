#!/bin/bash
# Demo script to show network monitoring in action

echo "🚀 Memento Network Monitoring Demo"
echo "=" * 50

echo "This demo will show you how to monitor network traffic for the Memento MCP system"
echo

# Step 1: Test basic network capture
echo "📋 Step 1: Testing basic network capture capabilities"
echo "🔍 Running: sudo tcpdump -i any -n -c 3 port 443"
echo "📡 This should capture HTTPS traffic..."
echo

# Capture a few packets
timeout 10s sudo tcpdump -i any -n -c 3 port 443 &
PID=$!

# Generate some traffic
sleep 2
curl -s https://httpbin.org/ip > /dev/null 2>&1 &

# Wait for capture
wait $PID

echo
echo "✅ Basic network capture test completed"
echo

# Step 2: Show how to use the network sniffer
echo "📋 Step 2: Using the Memento network sniffer"
echo "💡 To monitor traffic in real-time:"
echo "   Terminal 1: sudo python3 network_sniffer.py"
echo "   Terminal 2: python3 traffic_generator.py continuous"
echo

# Step 3: Show how to monitor MCP client traffic
echo "📋 Step 3: Monitoring MCP client traffic"
echo "💡 To monitor actual MCP client traffic:"
echo "   Terminal 1: sudo python3 network_sniffer.py"
echo "   Terminal 2: python3 memento_mcp_client_interactive_tracing.py"
echo

echo "🏁 Demo completed!"
echo "📖 See NETWORK_MONITORING.md for detailed instructions"
