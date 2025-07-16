#!/bin/bash
# Network traffic monitoring scripts for Memento MCP system

echo "🔍 Memento Network Traffic Monitoring Scripts"
echo "=============================================="

# Script 1: Monitor Azure OpenAI traffic
monitor_azure_traffic() {
    echo "📡 Monitoring Azure OpenAI HTTPS traffic..."
    echo "Press Ctrl+C to stop"
    
    sudo tcpdump -i any -n -s 0 -A \
        'host openai.azure.com or (dst port 443 and host contains "openai")' \
        -w azure_openai_traffic.pcap
}

# Script 2: Monitor MCP server traffic
monitor_mcp_traffic() {
    echo "🔌 Monitoring MCP server traffic on port 8000..."
    echo "Press Ctrl+C to stop"
    
    sudo tcpdump -i lo -n -s 0 -A \
        'port 8000' \
        -w mcp_server_traffic.pcap
}

# Script 3: Monitor all Memento traffic
monitor_all_traffic() {
    echo "🌐 Monitoring ALL Memento traffic..."
    echo "Press Ctrl+C to stop"
    
    sudo tcpdump -i any -n -s 0 -A \
        '(host openai.azure.com or dst port 443) or (port 8000)' \
        -w memento_all_traffic.pcap
}

# Script 4: Real-time traffic display
realtime_traffic() {
    echo "📊 Real-time traffic display..."
    echo "Press Ctrl+C to stop"
    
    # Monitor with timestamps and human-readable output
    sudo tcpdump -i any -n -t -s 0 \
        '(host openai.azure.com or dst port 443) or (port 8000)' \
        | while read line; do
            timestamp=$(date '+%H:%M:%S.%3N')
            echo "[$timestamp] $line"
        done
}

# Script 5: Network statistics
network_stats() {
    echo "📈 Network statistics for Memento..."
    
    # Show active connections
    echo "Active connections:"
    netstat -an | grep -E "8000|443" | head -20
    
    echo ""
    echo "Process network usage:"
    sudo netstat -tulpn | grep -E "python|8000|443" | head -10
}

# Script 6: Packet capture with filtering
filtered_capture() {
    echo "🎯 Filtered packet capture..."
    echo "Capturing HTTP/HTTPS headers and MCP messages"
    
    sudo tcpdump -i any -n -s 0 -A \
        '((port 443 or port 80) and (host openai.azure.com or host contains "openai")) or (port 8000)' \
        | grep -E "(POST|GET|HTTP|SSE|Content-Type|Authorization|user-agent)" \
        | while read line; do
            timestamp=$(date '+%H:%M:%S.%3N')
            echo "[$timestamp] $line"
        done
}

# Main menu
show_menu() {
    echo ""
    echo "Choose monitoring option:"
    echo "1. Monitor Azure OpenAI traffic only"
    echo "2. Monitor MCP server traffic only"
    echo "3. Monitor ALL Memento traffic"
    echo "4. Real-time traffic display"
    echo "5. Show network statistics"
    echo "6. Filtered packet capture (headers only)"
    echo "7. Exit"
}

# Main loop
while true; do
    show_menu
    read -p "Enter choice (1-7): " choice
    
    case $choice in
        1) monitor_azure_traffic ;;
        2) monitor_mcp_traffic ;;
        3) monitor_all_traffic ;;
        4) realtime_traffic ;;
        5) network_stats ;;
        6) filtered_capture ;;
        7) echo "👋 Goodbye!"; exit 0 ;;
        *) echo "Invalid choice. Please enter 1-7." ;;
    esac
    
    echo ""
    echo "Press Enter to continue..."
    read
done
