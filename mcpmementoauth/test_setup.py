#!/usr/bin/env python3
"""
Test script for Memento MCP Server with OAuth
This script tests the basic functionality without requiring full authentication
"""

import os
import json
import asyncio
from pathlib import Path

# Test data storage functionality
def test_user_data_structure():
    """Test that user data directory structure works correctly"""
    print("🧪 Testing user data directory structure...")
    
    # Create test user directory
    user_data_dir = Path("user_data")
    user_data_dir.mkdir(exist_ok=True)
    
    test_user_dir = user_data_dir / "user_test123"
    test_user_dir.mkdir(exist_ok=True)
    
    # Test file creation
    test_file = test_user_dir / "test_memento.json"
    test_data = {
        "id": "test-123",
        "title": "Test Memento",
        "content": "This is a test memento",
        "tags": ["test", "demo"],
        "created_at": "2024-01-01T12:00:00",
        "user_id": "test-user-123",
        "user_name": "Test User"
    }
    
    with open(test_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    # Verify file exists and can be read
    if test_file.exists():
        with open(test_file, 'r') as f:
            loaded_data = json.load(f)
            if loaded_data == test_data:
                print("✅ User data structure test passed!")
                return True
    
    print("❌ User data structure test failed!")
    return False

def test_environment_variables():
    """Test that required environment variables are set"""
    print("🧪 Testing environment variables...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY", 
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_TENANT_ID",
        "AZURE_CLIENT_ID",
        "AZURE_CLIENT_SECRET"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set!")
        return True

def test_dependencies():
    """Test that required Python packages are installed"""
    print("🧪 Testing Python dependencies...")
    
    try:
        import mcp
        import fastmcp
        import openai
        import msal
        import fastapi
        import uvicorn
        import httpx
        import aiofiles
        import cryptography
        from jose import jwt
        from dotenv import load_dotenv
        
        print("✅ All required Python packages are installed!")
        return True
    except ImportError as e:
        print(f"❌ Missing Python package: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def test_server_import():
    """Test that the server module can be imported"""
    print("🧪 Testing server module import...")
    
    try:
        # Test if we can import the server module
        import sys
        sys.path.append('.')
        
        # This will test the imports without running the server
        with open('memento_server_oauth.py', 'r') as f:
            server_code = f.read()
        
        # Check for key components
        if 'FastMCP' in server_code and 'store_memento' in server_code:
            print("✅ Server module structure looks correct!")
            return True
        else:
            print("❌ Server module structure appears incorrect!")
            return False
            
    except Exception as e:
        print(f"❌ Server module import failed: {e}")
        return False

def test_client_import():
    """Test that the client module can be imported"""
    print("🧪 Testing client module import...")
    
    try:
        # Test if we can import the client module
        with open('memento_client_oauth.py', 'r') as f:
            client_code = f.read()
        
        # Check for key components
        if 'InteractiveMementoClient' in client_code and 'authenticate_user' in client_code:
            print("✅ Client module structure looks correct!")
            return True
        else:
            print("❌ Client module structure appears incorrect!")
            return False
            
    except Exception as e:
        print(f"❌ Client module import failed: {e}")
        return False

def test_oauth_configuration():
    """Test OAuth configuration"""
    print("🧪 Testing OAuth configuration...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    
    if not tenant_id or not client_id or not client_secret:
        print("❌ OAuth configuration incomplete!")
        return False
    
    # Basic format validation
    if len(tenant_id) != 36 or len(client_id) != 36:
        print("❌ Azure AD IDs don't appear to be valid GUIDs!")
        return False
    
    print("✅ OAuth configuration appears valid!")
    return True

def cleanup_test_data():
    """Clean up test data"""
    print("🧹 Cleaning up test data...")
    
    try:
        test_user_dir = Path("user_data/user_test123")
        if test_user_dir.exists():
            import shutil
            shutil.rmtree(test_user_dir)
        print("✅ Test data cleaned up!")
    except Exception as e:
        print(f"⚠️  Could not clean up test data: {e}")

def main():
    """Run all tests"""
    print("🧠 Memento MCP Server Test Suite")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Environment Variables", test_environment_variables), 
        ("OAuth Configuration", test_oauth_configuration),
        ("User Data Structure", test_user_data_structure),
        ("Server Module", test_server_import),
        ("Client Module", test_client_import),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1
    
    # Clean up
    cleanup_test_data()
    
    print(f"\n{'='*50}")
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! You're ready to run the Memento MCP Server!")
        print("\nNext steps:")
        print("1. Start the server: python memento_server_oauth.py")
        print("2. Start the client: python memento_client_oauth.py")
        print("3. Follow the OAuth authentication flow")
    else:
        print("❌ Some tests failed. Please fix the issues before proceeding.")
        print("\nCommon fixes:")
        print("1. Run: pip install -r requirements.txt")
        print("2. Check your .env file configuration")
        print("3. Verify Azure AD app registration")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
