#!/bin/bash

# Setup script for Memento MCP Server with OAuth Authentication

echo "🧠 Setting up Memento MCP Server with OAuth Authentication"
echo "=" * 60

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create user data directory
echo "📁 Creating user data directory..."
mkdir -p user_data

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Please create a .env file with the following variables:"
    echo ""
    echo "# Azure OpenAI Configuration"
    echo "AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/"
    echo "AZURE_OPENAI_API_KEY=your-api-key"
    echo "AZURE_OPENAI_DEPLOYMENT=gpt-4"
    echo ""
    echo "# Azure AD Configuration"
    echo "AZURE_TENANT_ID=your-tenant-id"
    echo "AZURE_CLIENT_ID=your-client-id"
    echo "AZURE_CLIENT_SECRET=your-client-secret"
    echo ""
    echo "# MCP Server Configuration"
    echo "MCP_SERVER_URL=http://localhost:8000/sse"
    echo ""
    exit 1
fi

echo "✅ Setup complete!"
echo ""
echo "🚀 To start the server:"
echo "   python memento_server_oauth.py"
echo ""
echo "🖥️  To start the client:"
echo "   python memento_client_oauth.py"
echo ""
echo "📋 Don't forget to configure your Azure AD app registration!"
echo "   Run the server first to see the setup instructions."
