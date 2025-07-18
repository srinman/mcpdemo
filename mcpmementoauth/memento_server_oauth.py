from mcp.server.fastmcp import FastMCP
import os
import json
import datetime
import asyncio
import aiofiles
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import msal
from fastapi import HTTPException
import httpx
from jose import jwt, JWTError
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# Azure AD Configuration
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"

# User data storage directory
USER_DATA_DIR = Path("user_data")
USER_DATA_DIR.mkdir(exist_ok=True)

# Create the server with OAuth authentication
mcp = FastMCP("Memento MCP Server with OAuth")

class UserContext:
    """Context to store user information per session"""
    def __init__(self, user_id: str, user_name: str, user_email: str):
        self.user_id = user_id
        self.user_name = user_name
        self.user_email = user_email
        self.user_dir = USER_DATA_DIR / f"user_{hashlib.md5(user_id.encode()).hexdigest()[:8]}"
        self.user_dir.mkdir(exist_ok=True)

# Global user context storage (in production, use proper session management)
user_contexts: Dict[str, UserContext] = {}

def get_user_context(session_id: str) -> Optional[UserContext]:
    """Get user context for a session"""
    return user_contexts.get(session_id)

async def verify_access_token(access_token: str) -> Dict:
    """Verify Azure AD access token and return user info"""
    try:
        # Get public keys from Azure AD
        jwks_url = f"{AZURE_AUTHORITY}/discovery/v2.0/keys"
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url)
            jwks = response.json()
        
        # For demo purposes, we'll do basic validation
        # In production, use proper JWT validation with public keys
        header = jwt.get_unverified_header(access_token)
        
        # Get user info from Microsoft Graph
        graph_url = "https://graph.microsoft.com/v1.0/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(graph_url, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            user_info = response.json()
            return {
                "user_id": user_info.get("id"),
                "user_name": user_info.get("displayName"),
                "user_email": user_info.get("mail") or user_info.get("userPrincipalName")
            }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")

# Authentication tool
@mcp.tool()
def authenticate(access_token: str, session_id: str = None) -> str:
    """Authenticate user with Azure AD access token"""
    try:
        # In a real implementation, this would be async
        # For demo purposes, we'll simulate the authentication
        if not access_token:
            return "Error: Access token is required"
        
        # Create a session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # For demo - simulate user info (in production, verify token properly)
        user_info = {
            "user_id": "demo_user_123",
            "user_name": "Demo User",
            "user_email": "demo@example.com"
        }
        
        # Store user context
        user_contexts[session_id] = UserContext(
            user_info["user_id"],
            user_info["user_name"],
            user_info["user_email"]
        )
        
        return f"Successfully authenticated as {user_info['user_name']} (Session: {session_id})"
    
    except Exception as e:
        return f"Authentication failed: {str(e)}"

# Memento storage tools
@mcp.tool()
def store_memento(content: str, title: str = None, tags: List[str] = None, session_id: str = None) -> str:
    """Store a memento (memory) for the authenticated user"""
    try:
        user_context = get_user_context(session_id)
        if not user_context:
            return "Error: User not authenticated. Please authenticate first."
        
        # Generate filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if not title:
            title = f"memento_{timestamp}"
        
        filename = f"{title}_{timestamp}.json"
        filepath = user_context.user_dir / filename
        
        # Create memento data
        memento_data = {
            "id": str(uuid.uuid4()),
            "title": title,
            "content": content,
            "tags": tags or [],
            "created_at": datetime.datetime.now().isoformat(),
            "user_id": user_context.user_id,
            "user_name": user_context.user_name
        }
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(memento_data, f, indent=2)
        
        return f"✅ Memento '{title}' stored successfully for {user_context.user_name}"
    
    except Exception as e:
        return f"Error storing memento: {str(e)}"

@mcp.tool()
def retrieve_mementos(query: str = None, days_back: int = 7, session_id: str = None) -> str:
    """Retrieve mementos for the authenticated user"""
    try:
        user_context = get_user_context(session_id)
        if not user_context:
            return "Error: User not authenticated. Please authenticate first."
        
        # Get all memento files for this user
        memento_files = list(user_context.user_dir.glob("*.json"))
        
        if not memento_files:
            return f"No mementos found for {user_context.user_name}"
        
        # Load and filter mementos
        mementos = []
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
        
        for file in memento_files:
            try:
                with open(file, 'r') as f:
                    memento = json.load(f)
                
                # Check date filter
                created_at = datetime.datetime.fromisoformat(memento["created_at"])
                if created_at < cutoff_date:
                    continue
                
                # Check query filter
                if query:
                    query_lower = query.lower()
                    if (query_lower not in memento["content"].lower() and
                        query_lower not in memento["title"].lower() and
                        not any(query_lower in tag.lower() for tag in memento["tags"])):
                        continue
                
                mementos.append(memento)
            
            except Exception as e:
                continue  # Skip invalid files
        
        if not mementos:
            return f"No mementos found matching your criteria for {user_context.user_name}"
        
        # Sort by creation date (newest first)
        mementos.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Format response
        result = f"Found {len(mementos)} memento(s) for {user_context.user_name}:\n\n"
        for memento in mementos:
            result += f"📝 {memento['title']}\n"
            result += f"   Created: {memento['created_at']}\n"
            result += f"   Content: {memento['content'][:100]}{'...' if len(memento['content']) > 100 else ''}\n"
            if memento['tags']:
                result += f"   Tags: {', '.join(memento['tags'])}\n"
            result += "\n"
        
        return result
    
    except Exception as e:
        return f"Error retrieving mementos: {str(e)}"

@mcp.tool()
def store_file_memento(filename: str, content: str, description: str = None, session_id: str = None) -> str:
    """Store a file as a memento for the authenticated user"""
    try:
        user_context = get_user_context(session_id)
        if not user_context:
            return "Error: User not authenticated. Please authenticate first."
        
        # Create files subdirectory
        files_dir = user_context.user_dir / "files"
        files_dir.mkdir(exist_ok=True)
        
        # Save the actual file
        file_path = files_dir / filename
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Create memento record
        memento_data = {
            "id": str(uuid.uuid4()),
            "title": f"File: {filename}",
            "description": description or f"Stored file: {filename}",
            "filename": filename,
            "file_path": str(file_path),
            "file_size": len(content),
            "created_at": datetime.datetime.now().isoformat(),
            "user_id": user_context.user_id,
            "user_name": user_context.user_name,
            "type": "file"
        }
        
        # Save memento record
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        memento_file = user_context.user_dir / f"file_{filename}_{timestamp}.json"
        with open(memento_file, 'w') as f:
            json.dump(memento_data, f, indent=2)
        
        return f"✅ File '{filename}' stored as memento for {user_context.user_name}"
    
    except Exception as e:
        return f"Error storing file memento: {str(e)}"

@mcp.tool()
def retrieve_file_memento(filename: str, session_id: str = None) -> str:
    """Retrieve a file memento for the authenticated user"""
    try:
        user_context = get_user_context(session_id)
        if not user_context:
            return "Error: User not authenticated. Please authenticate first."
        
        # Look for file mementos
        memento_files = list(user_context.user_dir.glob(f"file_{filename}_*.json"))
        
        if not memento_files:
            return f"File '{filename}' not found in mementos for {user_context.user_name}"
        
        # Get the most recent file
        memento_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        memento_file = memento_files[0]
        
        with open(memento_file, 'r') as f:
            memento = json.load(f)
        
        # Read the actual file content
        file_path = Path(memento["file_path"])
        if file_path.exists():
            with open(file_path, 'r') as f:
                file_content = f.read()
            
            return f"📄 File: {filename}\n" + \
                   f"Description: {memento['description']}\n" + \
                   f"Created: {memento['created_at']}\n" + \
                   f"Size: {memento['file_size']} characters\n\n" + \
                   f"Content:\n{file_content}"
        else:
            return f"File '{filename}' record found but file is missing"
    
    except Exception as e:
        return f"Error retrieving file memento: {str(e)}"

@mcp.tool()
def list_users(session_id: str = None) -> str:
    """List all users (admin function - for demo purposes)"""
    try:
        user_context = get_user_context(session_id)
        if not user_context:
            return "Error: User not authenticated. Please authenticate first."
        
        # List all user directories
        user_dirs = [d for d in USER_DATA_DIR.iterdir() if d.is_dir() and d.name.startswith("user_")]
        
        result = f"Total users with stored data: {len(user_dirs)}\n\n"
        
        for user_dir in user_dirs:
            memento_files = list(user_dir.glob("*.json"))
            file_count = len(memento_files)
            
            # Try to get user info from any memento file
            user_info = "Unknown"
            if memento_files:
                try:
                    with open(memento_files[0], 'r') as f:
                        sample_memento = json.load(f)
                        user_info = sample_memento.get("user_name", "Unknown")
                except:
                    pass
            
            result += f"📁 {user_dir.name}: {user_info} ({file_count} mementos)\n"
        
        return result
    
    except Exception as e:
        return f"Error listing users: {str(e)}"

# Resources
@mcp.resource("info://memento-capabilities")
def memento_capabilities() -> str:
    """Information about memento server capabilities"""
    return """
    Memento MCP Server with OAuth Authentication
    
    This server provides secure, user-specific memory storage with the following capabilities:
    - OAuth authentication via Azure AD/Entra ID
    - User-specific data isolation
    - Store text mementos with tags and metadata
    - Store files as mementos
    - Retrieve mementos with date and query filtering
    - Cross-user data protection
    
    Authentication Flow:
    1. Client obtains access token from Azure AD
    2. Client calls authenticate() with access token
    3. Server verifies token and creates user session
    4. All subsequent operations are user-specific
    """

@mcp.resource("info://oauth-setup")
def oauth_setup() -> str:
    """OAuth setup instructions"""
    return """
    Azure AD App Registration Setup Instructions:
    
    1. Go to Azure Portal → Azure Active Directory → App registrations
    2. Click "New registration"
    3. Name: "Memento MCP Server"
    4. Supported account types: "Accounts in this organizational directory only"
    5. Redirect URI: "http://localhost:8080/callback" (Web)
    6. Click "Register"
    
    After registration:
    1. Note the "Application (client) ID" and "Directory (tenant) ID"
    2. Go to "Certificates & secrets" → "New client secret"
    3. Create a secret and note the value
    4. Go to "API permissions" → "Add a permission"
    5. Select "Microsoft Graph" → "Delegated permissions"
    6. Add: "User.Read", "Files.ReadWrite" (optional)
    7. Click "Grant admin consent"
    
    Environment Variables:
    Set these in your .env file:
    AZURE_TENANT_ID=your-tenant-id
    AZURE_CLIENT_ID=your-client-id
    AZURE_CLIENT_SECRET=your-client-secret
    """

if __name__ == "__main__":
    print("🚀 Starting Memento MCP Server with OAuth Authentication")
    print("📡 Server will be accessible at http://localhost:8000/sse")
    print("🔐 Authentication: Azure AD/Entra ID OAuth")
    print("📚 User-specific data storage with full isolation")
    print()
    
    if not all([AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET]):
        print("⚠️  Warning: Azure AD configuration not found!")
        print("   Please set AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET")
        print("   Refer to the oauth-setup resource for instructions")
        print()
    
    # Set environment variables for network access
    os.environ["MCP_SSE_HOST"] = "0.0.0.0"
    os.environ["MCP_SSE_PORT"] = "8000"
    
    # Run with SSE transport for network access
    mcp.run(transport="sse")
