# Network Traffic Monitoring Guide for Memento MCP System

This guide shows you how to monitor network traffic **outside** of your Memento application using system-level tools.

## 🔧 Quick Setup

### 1. Install Required Tools
```bash
# Install tcpdump (for packet capture)
sudo apt install tcpdump

# Install Wireshark (optional GUI tool)
sudo apt install wireshark

# Install netstat (usually pre-installed)
sudo apt install net-tools
```

### 2. Make Scripts Executable
```bash
chmod +x network_monitor.sh
chmod +x network_sniffer.py
```

## 🔍 Monitoring Options

### Option 1: Python Network Sniffer (Recommended)
```bash
sudo python3 network_sniffer.py
```

**Features:**
- Real-time traffic monitoring with colors
- Separate Azure OpenAI and MCP traffic detection
- Network statistics and process info
- Save traffic to .pcap files
- Monitor specific ports

**Sample Output:**
```
[14:30:25.123] 🧠 AZURE_OPENAI 📤 REQUEST (method: POST)
[14:30:25.456] 🧠 AZURE_OPENAI 📥 RESPONSE
[14:30:25.500] 🔌 MCP_SERVER 🔄 LOCAL
[14:30:25.678] 🔌 MCP_SERVER 🔄 LOCAL
```

### Option 2: Bash Script Monitor
```bash
./network_monitor.sh
```

**Features:**
- Multiple monitoring modes
- Packet capture to files
- Real-time display
- Network statistics

### Option 3: Direct tcpdump Commands

#### Monitor Azure OpenAI Traffic Only:
```bash
sudo tcpdump -i any -n -s 0 -A 'host openai.azure.com or dst port 443' -w azure_traffic.pcap
```

#### Monitor MCP Server Traffic Only:
```bash
sudo tcpdump -i lo -n -s 0 -A 'port 8000' -w mcp_traffic.pcap
```

#### Monitor Both (Real-time):
```bash
sudo tcpdump -i any -n -s 0 '(host openai.azure.com or dst port 443) or (port 8000)'
```

### Option 4: Wireshark (GUI)
```bash
sudo wireshark
```

**Filters to use:**
- Azure OpenAI: `tcp.port == 443 and ip.dst contains "openai.azure.com"`
- MCP Server: `tcp.port == 8000 and ip.dst == 127.0.0.1`
- Both: `(tcp.port == 443 and ip.dst contains "openai") or (tcp.port == 8000)`

## 📊 What You'll See

### Azure OpenAI Traffic:
- **Outgoing HTTPS requests** to `*.openai.azure.com:443`
- **POST requests** to `/chat/completions` endpoint
- **Request headers** with API authentication
- **Response data** with AI model outputs
- **Token usage** information

### MCP Server Traffic:
- **Local HTTP connections** to `localhost:8000`
- **Server-Sent Events (SSE)** communication
- **Tool discovery** requests (`list_tools`)
- **Tool execution** requests (`call_tool`)
- **JSON-formatted** request/response data

## 🚀 Usage Workflow

### 1. Start Traffic Monitoring
```bash
# Terminal 1: Start traffic monitoring
sudo python3 network_sniffer.py
# Choose option 1 for real-time monitoring
```

### 2. Run Memento Client
```bash
# Terminal 2: Start your Memento client
python3 memento_mcp_client_interactive.py
# OR
python3 memento_mcp_client_interactive_tracing.py
```

### 3. Interact with System
- Use the Memento client normally
- Watch real-time traffic in the monitoring terminal
- See Azure OpenAI and MCP server communications

### 4. Analyze Results
- View real-time stats in the sniffer
- Check saved .pcap files with Wireshark
- Analyze network patterns and performance

## 🎯 Example Traffic Analysis

### Typical Request Flow:
```
1. [14:30:25.123] 🧠 AZURE_OPENAI 📤 REQUEST (POST /chat/completions)
2. [14:30:25.456] 🧠 AZURE_OPENAI 📥 RESPONSE (tool_calls)
3. [14:30:25.500] 🔌 MCP_SERVER 🔄 LOCAL (call_tool: store_memory)
4. [14:30:25.678] 🔌 MCP_SERVER 🔄 LOCAL (response: success)
5. [14:30:25.700] 🧠 AZURE_OPENAI 📤 REQUEST (POST /chat/completions)
6. [14:30:25.890] 🧠 AZURE_OPENAI 📥 RESPONSE (final response)
```

### Performance Metrics:
- **Azure OpenAI latency**: ~300-400ms per request
- **MCP server latency**: ~50-100ms per request
- **Total interaction time**: ~800ms for complete flow
- **Data volumes**: Requests ~2-5KB, Responses ~1-3KB

## 🔧 Troubleshooting

### Permission Issues:
```bash
# If you get permission errors
sudo chmod +x network_*.py
sudo chmod +x network_*.sh

# For tcpdump access
sudo usermod -a -G wireshark $USER
# Log out and back in
```

### No Traffic Detected:
```bash
# Check if processes are running
ps aux | grep -E "(memento|mcp|python)"

# Check network connections
netstat -an | grep -E "(8000|443)"

# Test MCP server
curl -X GET http://localhost:8000/health
```

### High Traffic Volume:
```bash
# Use filtering to reduce noise
sudo tcpdump -i any -n 'port 8000' | grep -E "(POST|GET|HTTP)"

# Save to file instead of real-time display
sudo tcpdump -i any -n 'port 8000' -w traffic.pcap
```

## 📋 Network Security Notes

### What's Monitored:
- ✅ **Connection metadata** (IPs, ports, timestamps)
- ✅ **HTTP headers** (methods, content-types)
- ✅ **Traffic patterns** (request/response flows)
- ✅ **Performance metrics** (latency, throughput)

### What's Protected:
- 🔒 **API keys** are redacted in logs
- 🔒 **TLS-encrypted content** remains encrypted
- 🔒 **Authentication tokens** are sanitized
- 🔒 **User data** inside requests is truncated

This gives you complete visibility into your network traffic patterns while maintaining security! 🔍
