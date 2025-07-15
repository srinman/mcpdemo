# Memento MCP Server Program Flow - Technical Deep Dive

## 🎯 What Does the MCP Server Do?

The Memento MCP Server is a **specialized data storage service** that provides secure, user-isolated memory storage capabilities through the Model Context Protocol (MCP). It acts as the backend storage engine that:

- **Accepts tool calls** from MCP clients via Server-Sent Events (SSE)
- **Stores and retrieves** user data with complete isolation
- **Provides metadata management** (timestamps, tags, descriptions)
- **Handles natural language-friendly operations** through structured APIs

---

## 🏗️ Architecture Overview for Technical Developers

The MCP server uses a **file-based storage architecture** with network communication:

```
┌─────────────────────┐    HTTP/8000 (SSE)    ┌──────────────────────┐
│  MCP Clients        │◀──────────────────────│  Memento MCP Server  │
│  (Multiple)         │                       │  (FastMCP Framework) │
└─────────────────────┘                       └──────────────────────┘
                                                          │
                                                          │ File I/O
                                                          ▼
                                               ┌──────────────────────┐
                                               │  File System         │
                                               │  memento_storage/    │
                                               │  ├── alice/          │
                                               │  ├── bob/            │
                                               │  └── charlie/        │
                                               └──────────────────────┘
```

### Key Technical Concepts:

1. **FastMCP Framework**: Python framework for building MCP servers with decorators
2. **Server-Sent Events (SSE)**: HTTP-based protocol for real-time client-server communication
3. **User Isolation**: File system-level separation of user data
4. **Metadata Management**: JSON-based file metadata with full-text search
5. **Tool Registration**: Decorator-based tool registration system

---

## 🌐 Network Architecture & Connection Details

### **TCP Connection Handling & Server Binding**

#### 1. **Server Startup & Binding**
```python
# Server configuration
os.environ["MCP_SSE_HOST"] = "0.0.0.0"  # Bind to all interfaces
os.environ["MCP_SSE_PORT"] = "8000"     # Listen on port 8000

# Server startup
mcp.run(transport="sse")  # Start SSE server
```

**Network Details:**
- **Protocol**: HTTP with Server-Sent Events
- **Port**: 8000 (configurable via environment variable)
- **Binding**: 0.0.0.0 (accepts connections from any IP)
- **Transport**: Persistent SSE connections for real-time communication

#### 2. **Client Connection Acceptance**
```
1. Server starts → Binds to 0.0.0.0:8000 → Listens for connections
2. Client connects → TCP handshake → HTTP connection established
3. Client sends SSE request → Server upgrades to SSE → Persistent connection
4. Server registers client → Ready to receive tool calls
```

**Firewall Rules Needed:**
- **Inbound**: Allow connections to port 8000
- **Outbound**: No outbound connections required (server only)
- **Local**: Allow file system access for storage operations

#### 3. **Connection Lifecycle**
```
Client Request → SSE Connection → MCP Protocol → Tool Execution → Response
```

---

## 🔄 The Complete Server Technical Workflow

### **Phase 1: Server Initialization**
```python
# 1. Import and setup
from mcp.server.fastmcp import FastMCP
import os
import json
import datetime
from pathlib import Path

# 2. Create server instance
mcp = FastMCP("Memento MCP Server")

# 3. Setup storage directory
STORAGE_BASE_DIR = Path("memento_storage")
STORAGE_BASE_DIR.mkdir(exist_ok=True)

# 4. Load environment variables
load_dotenv(parent_dir / ".env")
```

### **Phase 2: Tool Registration**
```python
# Tools are registered using decorators
@mcp.tool()
def store_memory(user_id: str, content: str, filename: str = None, 
                description: str = "", tags: str = "") -> str:
    """Store content as a memory for a specific user"""
    # Tool implementation
    pass

@mcp.tool()
def retrieve_memories(user_id: str, query: str = "", time_filter: str = "", 
                     tag_filter: str = "", limit: int = 10) -> str:
    """Retrieve stored memories for a specific user"""
    # Tool implementation
    pass
```

### **Phase 3: Server Startup**
```python
if __name__ == "__main__":
    # Configure network settings
    os.environ["MCP_SSE_HOST"] = "0.0.0.0"
    os.environ["MCP_SSE_PORT"] = "8000"
    
    # Start server with SSE transport
    mcp.run(transport="sse")
```

### **Phase 4: Client Request Processing**

#### **Step 1: 🌐 Receive Client Request**
```
Client → Server (HTTP:8000 SSE)
POST /tool/store_memory
Content-Type: application/json

{
  "user_id": "alice",
  "content": "Meeting summary about Q4 planning...",
  "description": "Team meeting notes",
  "tags": "work,meeting"
}
```

#### **Step 2: 🔍 Request Validation**
```python
def store_memory(user_id: str, content: str, filename: str = None, 
                description: str = "", tags: str = "") -> str:
    # Input validation
    if not user_id.strip():
        return "Error: user_id is required"
    
    if not content.strip():
        return "Error: content cannot be empty"
    
    # Sanitize user_id to prevent directory traversal
    safe_user_id = re.sub(r'[^a-zA-Z0-9_-]', '_', user_id)
```

#### **Step 3: 📁 User Directory Management**
```python
def get_user_directory(user_id: str) -> Path:
    """Get or create user-specific directory"""
    # Sanitize user_id to prevent directory traversal
    safe_user_id = re.sub(r'[^a-zA-Z0-9_-]', '_', user_id)
    user_dir = STORAGE_BASE_DIR / safe_user_id
    user_dir.mkdir(exist_ok=True)  # Create if doesn't exist
    return user_dir
```

**File System Operations:**
```
memento_storage/
├── alice/          # User-specific directory
│   ├── 20240715_143052_meeting_notes.txt      # Content file
│   ├── 20240715_143052_meeting_notes.txt.meta # Metadata file
│   └── 20240715_144500_recipe.txt
└── bob/            # Separate user directory
    ├── 20240715_145000_quote.txt
    └── 20240715_145000_quote.txt.meta
```

#### **Step 4: 💾 File Storage Operations**
```python
def save_user_file(user_id: str, filename: str, content: str, 
                  description: str = "", tags: List[str] = None) -> str:
    """Save file for a specific user with metadata"""
    try:
        user_dir = get_user_directory(user_id)
        
        # Create timestamped filename to avoid conflicts
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        stored_filename = f"{timestamp}_{safe_filename}"
        
        file_path = user_dir / stored_filename
        
        # Save content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Create and save metadata
        metadata = create_file_metadata(filename, content, tags)
        metadata["stored_filename"] = stored_filename
        metadata["description"] = description
        
        metadata_path = user_dir / f"{stored_filename}.meta"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return f"Successfully stored '{filename}' for user {user_id} as {stored_filename}"
    except Exception as e:
        return f"Error storing file: {str(e)}"
```

#### **Step 5: 🏷️ Metadata Generation**
```python
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
```

**Metadata Example:**
```json
{
  "filename": "meeting_notes.txt",
  "timestamp": "2024-07-15T14:30:52.123456",
  "content_hash": "5d41402abc4b2a76b9719d911017c592",
  "size": 156,
  "tags": ["work", "meeting"],
  "description": "Q4 planning meeting notes",
  "stored_filename": "20240715_143052_meeting_notes.txt"
}
```

#### **Step 6: 📤 Response Generation**
```python
# Server returns success response
return f"Successfully stored '{filename}' for user {user_id} as {stored_filename}"
```

**Network Response:**
```json
{
  "content": [{
    "type": "text",
    "text": "Successfully stored 'meeting_notes.txt' for user alice as 20240715_143052_meeting_notes.txt"
  }]
}
```

---

## 🔍 Data Retrieval Workflow

### **Search and Retrieval Process**

#### **Step 1: 🔍 Search Request**
```
Client → Server (HTTP:8000 SSE)
POST /tool/retrieve_memories
Content-Type: application/json

{
  "user_id": "alice",
  "query": "meeting",
  "time_filter": "last_week",
  "tag_filter": "work",
  "limit": 10
}
```

#### **Step 2: 🗂️ File System Search**
```python
def search_user_files(user_id: str, query: str = "", time_filter: str = "", 
                     tag_filter: str = "") -> List[Dict[str, Any]]:
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
                
                # Apply time filter
                if time_filter:
                    file_time = datetime.datetime.fromisoformat(metadata["timestamp"])
                    now = datetime.datetime.now()
                    
                    if time_filter == "last_week":
                        week_ago = now - datetime.timedelta(days=7)
                        if file_time < week_ago:
                            continue
                
                # Apply tag filter
                if tag_filter and tag_filter not in metadata.get("tags", []):
                    continue
                
                # Apply content search
                if query:
                    query_lower = query.lower()
                    searchable_text = f"{metadata['filename']} {metadata.get('description', '')}"
                    
                    # Search in file content
                    content_file = user_dir / metadata["stored_filename"]
                    if content_file.exists():
                        with open(content_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        searchable_text += f" {content}"
                    
                    if query_lower not in searchable_text.lower():
                        continue
                
                results.append(metadata)
            except Exception as e:
                continue
        
        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        return results
    except Exception as e:
        return []
```

#### **Step 3: 📊 Result Formatting**
```python
def retrieve_memories(user_id: str, query: str = "", time_filter: str = "", 
                     tag_filter: str = "", limit: int = 10) -> str:
    """Retrieve stored memories for a specific user"""
    results = search_user_files(user_id, query, time_filter, tag_filter)
    
    if not results:
        return f"No memories found for user {user_id}"
    
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
```

---

## 🛠️ Available MCP Tools

### **1. store_memory**
```python
@mcp.tool()
def store_memory(user_id: str, content: str, filename: str = None, 
                description: str = "", tags: str = "") -> str:
    """Store content as a memory for a specific user"""
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"memory_{timestamp}.txt"
    
    # Parse tags from comma-separated string
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
    
    return save_user_file(user_id, filename, content, description, tag_list)
```

### **2. retrieve_memories**
```python
@mcp.tool()
def retrieve_memories(user_id: str, query: str = "", time_filter: str = "", 
                     tag_filter: str = "", limit: int = 10) -> str:
    """Retrieve stored memories for a specific user"""
    # Search with filters
    results = search_user_files(user_id, query, time_filter, tag_filter)
    
    # Format and return results
    return format_search_results(results, user_id, limit)
```

### **3. get_memory_content**
```python
@mcp.tool()
def get_memory_content(user_id: str, memory_id: str) -> str:
    """Get the full content of a specific memory"""
    try:
        user_dir = get_user_directory(user_id)
        file_path = user_dir / memory_id
        
        if not file_path.exists():
            return f"File {memory_id} not found for user {user_id}"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"
```

### **4. delete_memory**
```python
@mcp.tool()
def delete_memory(user_id: str, memory_id: str) -> str:
    """Delete a specific memory for a user"""
    try:
        user_dir = get_user_directory(user_id)
        
        # Delete both content and metadata files
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
```

### **5. get_user_stats**
```python
@mcp.tool()
def get_user_stats(user_id: str) -> str:
    """Get statistics about stored memories for a user"""
    try:
        user_dir = get_user_directory(user_id)
        meta_files = list(user_dir.glob("*.meta"))
        
        if not meta_files:
            return f"No memories found for user {user_id}"
        
        total_files = len(meta_files)
        total_size = 0
        all_tags = set()
        oldest_time = None
        newest_time = None
        
        for meta_file in meta_files:
            with open(meta_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            total_size += metadata.get('size', 0)
            all_tags.update(metadata.get('tags', []))
            
            file_time = datetime.datetime.fromisoformat(metadata["timestamp"])
            if oldest_time is None or file_time < oldest_time:
                oldest_time = file_time
            if newest_time is None or file_time > newest_time:
                newest_time = file_time
        
        stats = f"Memory statistics for user {user_id}:\n"
        stats += f"- Total memories: {total_files}\n"
        stats += f"- Total size: {total_size:,} characters\n"
        stats += f"- Unique tags: {len(all_tags)}\n"
        stats += f"- Available tags: {', '.join(sorted(all_tags))}\n"
        stats += f"- Oldest memory: {oldest_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        stats += f"- Newest memory: {newest_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return stats
    except Exception as e:
        return f"Error getting user stats: {str(e)}"
```

### **6. list_users**
```python
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
```

---

## 🔐 Security Implementation

### **Input Sanitization**
```python
def get_user_directory(user_id: str) -> Path:
    """Get or create user-specific directory"""
    # Sanitize user_id to prevent directory traversal
    safe_user_id = re.sub(r'[^a-zA-Z0-9_-]', '_', user_id)
    user_dir = STORAGE_BASE_DIR / safe_user_id
    user_dir.mkdir(exist_ok=True)
    return user_dir

def save_user_file(user_id: str, filename: str, content: str, 
                  description: str = "", tags: List[str] = None) -> str:
    # Sanitize filename to prevent path traversal
    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    stored_filename = f"{timestamp}_{safe_filename}"
```

### **User Isolation**
```python
# Each user gets their own directory
user_dir = STORAGE_BASE_DIR / safe_user_id  # e.g., memento_storage/alice/

# All operations are scoped to user directory
def search_user_files(user_id: str, ...):
    user_dir = get_user_directory(user_id)  # Only access user's files
    # Search only within user's directory
```

### **Error Handling**
```python
try:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
except PermissionError:
    return "Error: Permission denied accessing file"
except OSError as e:
    return f"Error: File system error: {str(e)}"
except Exception as e:
    return f"Error storing file: {str(e)}"
```

---

## 📊 MCP Resources & Prompts

### **Resources (Server Capabilities)**
```python
@mcp.resource("info://server-capabilities")
def server_capabilities() -> str:
    """Information about the Memento MCP server's capabilities"""
    return """
    Memento MCP Server - Personal Memory Storage System
    
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
    """
```

### **Prompts (User Guidance)**
```python
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
```

---

## 🚀 Production Considerations

### **Performance Optimization**
```python
# File system caching
from functools import lru_cache

@lru_cache(maxsize=128)
def get_user_directory(user_id: str) -> Path:
    """Cached user directory lookup"""
    safe_user_id = re.sub(r'[^a-zA-Z0-9_-]', '_', user_id)
    user_dir = STORAGE_BASE_DIR / safe_user_id
    user_dir.mkdir(exist_ok=True)
    return user_dir

# Batch operations for large datasets
def batch_search_files(user_id: str, batch_size: int = 100):
    """Process files in batches to avoid memory issues"""
    user_dir = get_user_directory(user_id)
    meta_files = list(user_dir.glob("*.meta"))
    
    for i in range(0, len(meta_files), batch_size):
        batch = meta_files[i:i + batch_size]
        yield process_batch(batch)
```

### **Error Handling & Logging**
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def store_memory(user_id: str, content: str, **kwargs) -> str:
    """Store memory with comprehensive error handling"""
    try:
        logger.info(f"Storing memory for user {user_id}, size: {len(content)} chars")
        
        # Validation
        if not user_id.strip():
            logger.warning("Empty user_id provided")
            return "Error: user_id is required"
        
        # Store file
        result = save_user_file(user_id, filename, content, description, tags)
        logger.info(f"Successfully stored memory for user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error storing memory for user {user_id}: {str(e)}")
        return f"Error storing file: {str(e)}"
```

### **Scalability Considerations**
```python
# Database integration for large-scale deployments
class DatabaseMetadataStore:
    def __init__(self, db_url: str):
        self.db = create_database_connection(db_url)
    
    def store_metadata(self, user_id: str, metadata: dict):
        """Store metadata in database instead of JSON files"""
        query = """
        INSERT INTO file_metadata (user_id, filename, timestamp, tags, description)
        VALUES (?, ?, ?, ?, ?)
        """
        self.db.execute(query, (user_id, metadata['filename'], 
                               metadata['timestamp'], json.dumps(metadata['tags']),
                               metadata['description']))
    
    def search_metadata(self, user_id: str, **filters):
        """Search metadata with database queries"""
        # Implement SQL-based search with indexes
        pass

# Configuration for production
class ProductionConfig:
    STORAGE_BASE_DIR = Path("/var/lib/memento/storage")
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_FILES_PER_USER = 10000
    ENABLE_COMPRESSION = True
    BACKUP_ENABLED = True
    BACKUP_INTERVAL = 3600  # 1 hour
```

---

## 🎯 Summary

The Memento MCP Server is a **robust file storage service** that provides:

### **Key Technical Features:**

1. **MCP Protocol Implementation**: Standards-compliant tool registration and execution
2. **User Data Isolation**: File system-level separation with sanitized user IDs
3. **Metadata Management**: JSON-based metadata with full-text search capabilities
4. **Network Communication**: SSE-based real-time communication with clients
5. **Security**: Input validation, path sanitization, and error handling
6. **Extensibility**: Decorator-based tool registration for easy expansion

### **Architecture Benefits:**

- **Scalability**: File-based storage that can be upgraded to database backend
- **Security**: Complete user isolation and input sanitization
- **Performance**: Efficient file system operations with caching support
- **Maintainability**: Clean separation of concerns with FastMCP framework
- **Reliability**: Comprehensive error handling and logging

This server demonstrates how to build production-ready MCP services that can handle real-world data storage requirements while maintaining security and performance! 🌟

---

## 📚 Further Reading

- **FastMCP Framework**: [FastMCP Documentation](https://github.com/modelcontextprotocol/python-sdk)
- **MCP Protocol**: [Model Context Protocol Specification](https://github.com/modelcontextprotocol/specification)
- **Server-Sent Events**: [MDN SSE Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- **Python File I/O**: [Python pathlib Documentation](https://docs.python.org/3/library/pathlib.html)
