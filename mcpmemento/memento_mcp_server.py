from mcp.server.fastmcp import FastMCP
import os
import json
import datetime
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from parent directory
parent_dir = Path(__file__).parent.parent
env_path = parent_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env file from {env_path}")
else:
    print("⚠️  .env file not found in parent directory")

# Create the server with memento capabilities
mcp = FastMCP("Memento MCP Server")

# Base directory for storing user files
STORAGE_BASE_DIR = Path("memento_storage")
STORAGE_BASE_DIR.mkdir(exist_ok=True)

def get_user_directory(user_id: str) -> Path:
    """Get or create user-specific directory"""
    # Sanitize user_id to prevent directory traversal
    safe_user_id = re.sub(r'[^a-zA-Z0-9_-]', '_', user_id)
    user_dir = STORAGE_BASE_DIR / safe_user_id
    user_dir.mkdir(exist_ok=True)
    return user_dir

def create_file_metadata(filename: str, content: str, tags: List[str] = None) -> Dict[str, Any]:
    """Create metadata for stored files"""
    timestamp = datetime.datetime.now().isoformat()
    content_hash = hashlib.md5(content.encode()).hexdigest()
    
    return {
        "filename": filename,
        "timestamp": timestamp,
        "content_hash": content_hash,
        "size": len(content),
        "tags": tags or [],
        "description": ""
    }

def save_user_file(user_id: str, filename: str, content: str, description: str = "", tags: List[str] = None) -> str:
    """Save file for a specific user with metadata"""
    try:
        user_dir = get_user_directory(user_id)
        
        # Create timestamped filename to avoid conflicts
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        stored_filename = f"{timestamp}_{safe_filename}"
        
        file_path = user_dir / stored_filename
        
        # Save content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Save metadata
        metadata = create_file_metadata(filename, content, tags)
        metadata["stored_filename"] = stored_filename
        metadata["description"] = description
        
        metadata_path = user_dir / f"{stored_filename}.meta"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return f"Successfully stored '{filename}' for user {user_id} as {stored_filename}"
    except Exception as e:
        return f"Error storing file: {str(e)}"

def search_user_files(user_id: str, query: str = "", time_filter: str = "", tag_filter: str = "") -> List[Dict[str, Any]]:
    """Search files for a specific user"""
    try:
        user_dir = get_user_directory(user_id)
        if not user_dir.exists():
            return []
        
        results = []
        
        # Get all metadata files
        for meta_file in user_dir.glob("*.meta"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Apply filters
                if time_filter:
                    file_time = datetime.datetime.fromisoformat(metadata["timestamp"])
                    now = datetime.datetime.now()
                    
                    if time_filter == "today":
                        if file_time.date() != now.date():
                            continue
                    elif time_filter == "yesterday":
                        yesterday = now.date() - datetime.timedelta(days=1)
                        if file_time.date() != yesterday:
                            continue
                    elif time_filter == "last_week":
                        week_ago = now - datetime.timedelta(days=7)
                        if file_time < week_ago:
                            continue
                    elif time_filter == "last_month":
                        month_ago = now - datetime.timedelta(days=30)
                        if file_time < month_ago:
                            continue
                
                if tag_filter and tag_filter not in metadata.get("tags", []):
                    continue
                
                if query:
                    # Search in filename, description, and content
                    query_lower = query.lower()
                    searchable_text = f"{metadata['filename']} {metadata.get('description', '')}"
                    
                    # Also search in file content
                    content_file = user_dir / metadata["stored_filename"]
                    if content_file.exists():
                        try:
                            with open(content_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            searchable_text += f" {content}"
                        except:
                            pass
                    
                    if query_lower not in searchable_text.lower():
                        continue
                
                results.append(metadata)
            except Exception as e:
                print(f"Error reading metadata file {meta_file}: {e}")
                continue
        
        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        return results
    except Exception as e:
        print(f"Error searching files: {e}")
        return []

def get_user_file_content(user_id: str, stored_filename: str) -> str:
    """Get content of a specific file for a user"""
    try:
        user_dir = get_user_directory(user_id)
        file_path = user_dir / stored_filename
        
        if not file_path.exists():
            return f"File {stored_filename} not found for user {user_id}"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

# MCP TOOLS

@mcp.tool()
def store_memory(user_id: str, content: str, filename: str = None, description: str = "", tags: str = "") -> str:
    """Store content as a memory for a specific user
    
    Args:
        user_id: Identifier for the user (e.g., 'alice', 'bob')
        content: The content to store
        filename: Optional filename (will be generated if not provided)
        description: Optional description of the content
        tags: Comma-separated tags for categorization
    """
    if not user_id.strip():
        return "Error: user_id is required"
    
    if not content.strip():
        return "Error: content cannot be empty"
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"memory_{timestamp}.txt"
    
    # Parse tags
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
    
    return save_user_file(user_id, filename, content, description, tag_list)

@mcp.tool()
def retrieve_memories(user_id: str, query: str = "", time_filter: str = "", tag_filter: str = "", limit: int = 10) -> str:
    """Retrieve stored memories for a specific user
    
    Args:
        user_id: Identifier for the user
        query: Search query to match against content, filename, or description
        time_filter: Time filter (today, yesterday, last_week, last_month)
        tag_filter: Filter by specific tag
        limit: Maximum number of results to return
    """
    if not user_id.strip():
        return "Error: user_id is required"
    
    results = search_user_files(user_id, query, time_filter, tag_filter)
    
    if not results:
        filter_desc = []
        if query:
            filter_desc.append(f"query '{query}'")
        if time_filter:
            filter_desc.append(f"time filter '{time_filter}'")
        if tag_filter:
            filter_desc.append(f"tag '{tag_filter}'")
        
        filter_text = " with " + ", ".join(filter_desc) if filter_desc else ""
        return f"No memories found for user {user_id}{filter_text}"
    
    # Limit results
    results = results[:limit]
    
    output = f"Found {len(results)} memories for user {user_id}:\n\n"
    
    for i, result in enumerate(results, 1):
        timestamp = datetime.datetime.fromisoformat(result["timestamp"])
        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        output += f"{i}. {result['filename']}\n"
        output += f"   Stored: {formatted_time}\n"
        output += f"   Size: {result['size']} characters\n"
        
        if result.get('description'):
            output += f"   Description: {result['description']}\n"
        
        if result.get('tags'):
            output += f"   Tags: {', '.join(result['tags'])}\n"
        
        output += f"   ID: {result['stored_filename']}\n\n"
    
    return output.strip()

@mcp.tool()
def get_memory_content(user_id: str, memory_id: str) -> str:
    """Get the full content of a specific memory
    
    Args:
        user_id: Identifier for the user
        memory_id: The stored filename ID of the memory
    """
    if not user_id.strip():
        return "Error: user_id is required"
    
    if not memory_id.strip():
        return "Error: memory_id is required"
    
    return get_user_file_content(user_id, memory_id)

@mcp.tool()
def list_users() -> str:
    """List all users who have stored memories"""
    try:
        if not STORAGE_BASE_DIR.exists():
            return "No users found (storage directory doesn't exist)"
        
        users = []
        for user_dir in STORAGE_BASE_DIR.iterdir():
            if user_dir.is_dir():
                file_count = len(list(user_dir.glob("*.meta")))
                if file_count > 0:
                    users.append(f"{user_dir.name} ({file_count} memories)")
        
        if not users:
            return "No users with stored memories found"
        
        return "Users with stored memories:\n" + "\n".join(f"- {user}" for user in users)
    except Exception as e:
        return f"Error listing users: {str(e)}"

@mcp.tool()
def delete_memory(user_id: str, memory_id: str) -> str:
    """Delete a specific memory for a user
    
    Args:
        user_id: Identifier for the user
        memory_id: The stored filename ID of the memory to delete
    """
    if not user_id.strip():
        return "Error: user_id is required"
    
    if not memory_id.strip():
        return "Error: memory_id is required"
    
    try:
        user_dir = get_user_directory(user_id)
        
        # Delete content file
        content_file = user_dir / memory_id
        meta_file = user_dir / f"{memory_id}.meta"
        
        if not content_file.exists():
            return f"Memory {memory_id} not found for user {user_id}"
        
        content_file.unlink()
        if meta_file.exists():
            meta_file.unlink()
        
        return f"Successfully deleted memory {memory_id} for user {user_id}"
    except Exception as e:
        return f"Error deleting memory: {str(e)}"

@mcp.tool()
def get_user_stats(user_id: str) -> str:
    """Get statistics about stored memories for a user
    
    Args:
        user_id: Identifier for the user
    """
    if not user_id.strip():
        return "Error: user_id is required"
    
    try:
        user_dir = get_user_directory(user_id)
        if not user_dir.exists():
            return f"No memories found for user {user_id}"
        
        meta_files = list(user_dir.glob("*.meta"))
        
        if not meta_files:
            return f"No memories found for user {user_id}"
        
        total_files = len(meta_files)
        total_size = 0
        all_tags = set()
        oldest_time = None
        newest_time = None
        
        for meta_file in meta_files:
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                total_size += metadata.get('size', 0)
                all_tags.update(metadata.get('tags', []))
                
                file_time = datetime.datetime.fromisoformat(metadata["timestamp"])
                if oldest_time is None or file_time < oldest_time:
                    oldest_time = file_time
                if newest_time is None or file_time > newest_time:
                    newest_time = file_time
            except Exception:
                continue
        
        stats = f"Memory statistics for user {user_id}:\n"
        stats += f"- Total memories: {total_files}\n"
        stats += f"- Total size: {total_size:,} characters\n"
        stats += f"- Unique tags: {len(all_tags)}\n"
        
        if all_tags:
            stats += f"- Available tags: {', '.join(sorted(all_tags))}\n"
        
        if oldest_time and newest_time:
            stats += f"- Oldest memory: {oldest_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            stats += f"- Newest memory: {newest_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return stats
    except Exception as e:
        return f"Error getting user stats: {str(e)}"

# RESOURCES

@mcp.resource("info://server-capabilities")
def server_capabilities() -> str:
    """Information about the Memento MCP server's capabilities"""
    return """
    Memento MCP Server - Personal Memory Storage System
    
    This server provides secure, user-isolated memory storage capabilities:
    
    Core Features:
    - Store arbitrary text content as "memories" for specific users
    - Retrieve memories with flexible search and filtering
    - User isolation - each user's data is completely separate
    - Metadata tracking (timestamps, tags, descriptions, file sizes)
    - Natural language queries for memory operations
    
    Storage Features:
    - Automatic timestamping and file versioning
    - Tag-based categorization
    - Time-based filtering (today, yesterday, last week, last month)
    - Content search across filenames, descriptions, and file contents
    - File size and usage statistics
    
    Security:
    - User data isolation (no cross-user access)
    - Sanitized user IDs and filenames
    - Secure file storage in user-specific directories
    
    Use Cases:
    - Personal note-taking and memory storage
    - Document archival with searchable metadata
    - Multi-user content management
    - Natural language-driven file operations
    """

@mcp.resource("info://usage-examples")
def usage_examples() -> str:
    """Examples of how to use the Memento MCP server"""
    return """
    Example Natural Language Commands:
    
    Storing Memories:
    - "Hey memento, store this file content for user alice"
    - "Save this note about the meeting for bob with tags 'work,important'"
    - "Remember this recipe for user chef with description 'chocolate cake'"
    
    Retrieving Memories:
    - "Show me what alice stored last week"
    - "Find all memories for bob tagged with 'work'"
    - "What did chef save yesterday?"
    - "Get all memories for alice containing 'project'"
    
    Managing Memories:
    - "List all users who have stored data"
    - "Show statistics for user alice"
    - "Delete memory ID 20240714_143052_note.txt for bob"
    - "Get the content of memory 20240714_120000_recipe.txt for chef"
    
    Example Tool Calls:
    1. store_memory(user_id="alice", content="Meeting notes...", description="Team meeting", tags="work,meeting")
    2. retrieve_memories(user_id="alice", query="project", time_filter="last_week")
    3. get_memory_content(user_id="alice", memory_id="20240714_143052_meeting.txt")
    4. get_user_stats(user_id="alice")
    5. list_users()
    """

# PROMPTS

@mcp.prompt(description="Help user store a memory")
def store_memory_prompt() -> str:
    return """I can help you store memories! Please provide:
1. Your user ID (e.g., 'alice', 'bob', 'your_name')
2. The content you want to store
3. Optional: filename, description, and tags for better organization

Example: "Store this meeting summary for user alice with tags 'work,important'"
"""

@mcp.prompt(description="Help user retrieve memories")
def retrieve_memory_prompt() -> str:
    return """I can help you find your stored memories! Please provide:
1. Your user ID
2. Optional search criteria:
   - Search query (keywords to find)
   - Time filter (today, yesterday, last_week, last_month)
   - Tag filter (specific tag to filter by)

Example: "Show me all memories for alice from last week tagged with 'work'"
"""

if __name__ == "__main__":
    print("🧠 Starting Memento MCP Server")
    print("📁 Personal Memory Storage System")
    print("🔐 User-isolated file storage")
    print(f"💾 Storage directory: {STORAGE_BASE_DIR.absolute()}")
    print("📡 Server will be accessible at http://0.0.0.0:8000/sse")
    print()
    print("🔧 Available tools:")
    print("  - store_memory: Store content for a user")
    print("  - retrieve_memories: Search and list memories")
    print("  - get_memory_content: Get full content of a memory")
    print("  - list_users: List all users with stored data")
    print("  - delete_memory: Delete a specific memory")
    print("  - get_user_stats: Get storage statistics for a user")
    print()

    # Set environment variables for network access
    host = os.getenv("MCP_SSE_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_SSE_PORT", "8000"))
    
    print(f"🚀 Starting server on {host}:{port}")
    
    # Run with SSE transport for network access
    mcp.run(transport="sse", host=host, port=port)
