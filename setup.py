#!/usr/bin/env python3
"""
Setup script for Azure OpenAI + MCP integration
"""

import os
import sys

def create_env_file():
    """Create a .env file template"""
    env_content = """# Azure OpenAI Configuration
# Replace these with your actual Azure OpenAI credentials

AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Optional: MCP Server Configuration
MCP_SERVER_URL=http://localhost:8000/sse
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file template")
    print("📝 Please edit .env with your Azure OpenAI credentials")

def check_requirements():
    """Check if required packages are installed"""
    required_packages = ['openai', 'mcp', 'psutil']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("🔧 Install them with: pip install " + " ".join(missing_packages))
        return False
    else:
        print("✅ All required packages are installed")
        return True

def main():
    print("🚀 Azure OpenAI + MCP Integration Setup")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Please install missing packages first")
        sys.exit(1)
    
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        create_env_file()
    else:
        print("✅ .env file already exists")
    
    print("\n📋 Setup Instructions:")
    print("1. Edit .env file with your Azure OpenAI credentials")
    print("2. Start the MCP server: python azure_mcp_server.py")
    print("3. In another terminal, run: python azure_openai_mcp_client.py")
    print("\n🔗 How to get Azure OpenAI credentials:")
    print("- Go to Azure Portal → Azure OpenAI → Your Resource")
    print("- Copy the Endpoint and API Key")
    print("- Note your deployment name (e.g., gpt-4o-mini)")
    
    print("\n🎯 Demo Mode:")
    print("If you don't have Azure OpenAI credentials, the client will run in demo mode")
    print("showing what the interaction would look like.")

if __name__ == "__main__":
    main()
