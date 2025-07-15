#!/bin/bash

# Memento MCP System Startup Script

echo "🧠 Memento - Personal Memory Storage System"
echo "=========================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip is required but not found"
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    if command -v pip3 &> /dev/null; then
        pip3 install -r requirements.txt
    else
        pip install -r requirements.txt
    fi
    echo ""
fi

# Check if .env file exists in parent directory
if [ ! -f "../.env" ]; then
    echo "⚠️  .env file not found in parent directory"
    echo "   Please create ../.env with your Azure OpenAI credentials:"
    echo "   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com"
    echo "   AZURE_OPENAI_API_KEY=your-api-key"  
    echo "   AZURE_OPENAI_DEPLOYMENT=your-deployment-name"
    echo ""
    echo "🎭 You can still run the demo without credentials"
    echo ""
fi

echo "🚀 What would you like to do?"
echo ""
echo "1. Run demo (no Azure OpenAI required)"
echo "2. Start MCP server"
echo "3. Start interactive client" 
echo "4. Start both server and client"
echo "5. Exit"
echo ""

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🎭 Running Memento demo..."
        python3 demo.py
        ;;
    2)
        echo ""
        echo "🖥️  Starting Memento MCP server..."
        echo "   Server will be available at http://localhost:8000/sse"
        echo "   Press Ctrl+C to stop"
        echo ""
        python3 memento_mcp_server.py
        ;;
    3)
        echo ""
        echo "💬 Starting interactive client..."
        echo "   Make sure the MCP server is running first!"
        echo ""
        python3 memento_mcp_client_interactive.py
        ;;
    4)
        echo ""
        echo "🚀 Starting both server and client..."
        echo "   Server will start in background"
        echo "   Client will start in foreground"
        echo ""
        
        # Start server in background
        python3 memento_mcp_server.py &
        SERVER_PID=$!
        
        # Wait a moment for server to start
        sleep 3
        
        # Start client
        python3 memento_mcp_client_interactive.py
        
        # Kill server when client exits
        kill $SERVER_PID 2>/dev/null
        ;;
    5)
        echo ""
        echo "👋 Goodbye!"
        ;;
    *)
        echo ""
        echo "❌ Invalid choice. Please run the script again."
        ;;
esac
