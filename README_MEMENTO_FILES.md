# Memento: AI Memory System (File-Based Storage)

## 🧠 Overview

**Memento: AI Memory** is an intelligent memory management system built using the Model Context Protocol (MCP) with **file-based storage**. Unlike the database version, this implementation stores each user's memories in **separate JSON files**, providing enhanced data isolation and simpler deployment.

**Catchphrase:** *"Hey Memento"* - Your AI memory assistant

## 🎯 Key Features

### **File-Based Architecture**
- **Individual JSON files** for each user (complete data separation)
- **Atomic file operations** with locking for concurrency safety
- **Safe filename generation** to prevent path traversal attacks
- **No database dependencies** - just filesystem storage

### **Natural Language Memory Management**
- **Store memories** with commands like "Hey Memento, remember that..."
- **Recall memories** with queries like "What did I ask you to remember last week?"
- **Smart categorization** (work, personal, ideas, tasks, notes, contacts, events)
- **Importance levels** (1-10 scale for prioritizing memories)

### **User Data Separation**
- Each user gets their own JSON file: `{safe_user_id}_{hash}.json`
- User identification based on system username and hostname
- **Zero cross-user data leakage** (file-level isolation)
- Server controls all file access and ownership

### **Intelligent Search and Retrieval**
- **Time-based queries**: "last week", "this month", "this year"
- **Category filtering**: work memories, personal memories, etc.
- **Full-text search** across memory content and tags
- **Memory statistics** and summaries per user

### **Azure OpenAI Integration**
- **Natural language understanding** for memory commands
- **Conversational interface** for easy interaction
- **Two-phase processing** for intelligent memory management
- **Context-aware responses** based on stored memories

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│   Azure OpenAI  │◄──►│  Memento Client  │◄──►│ Memento Server  │
│                 │    │   (Files Mode)   │    │   (Files MCP)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                         │
                                │                         ▼
                                │                ┌─────────────────┐
                                │                │  File Manager   │
                                │                │                 │
                                │                └─────────────────┘
                                │                         │
                                └─────────────────────────▼
                                                ┌─────────────────┐
                                                │ User JSON Files │
                                                │                 │
                                                │ alice_12ab.json │
                                                │ bob_34cd.json   │
                                                │ charlie_56ef... │
                                                └─────────────────┘
```

## 📁 File Structure

### **Memory Directory Layout**
```
memento_memories/
├── alice_laptop_a1b2c3d4.json      # Alice's memories
├── bob_desktop_e5f6g7h8.json       # Bob's memories
├── charlie_work_i9j0k1l2.json      # Charlie's memories
└── ...
```

### **Individual User File Format**
```json
{
  "user_id": "alice@laptop",
  "last_updated": "2025-07-13T10:30:00.123456",
  "total_memories": 3,
  "memories": [
    {
      "id": 1,
      "content": "Remember to buy groceries: milk, bread, eggs",
      "category": "tasks",
      "tags": ["shopping", "food"],
      "importance": 7,
      "metadata": {},
      "created_at": "2025-07-13T09:15:00.123456",
      "updated_at": "2025-07-13T09:15:00.123456"
    },
    {
      "id": 2,
      "content": "Meeting with team lead tomorrow at 3 PM",
      "category": "work",
      "tags": ["meeting", "work"],
      "importance": 8,
      "metadata": {},
      "created_at": "2025-07-13T10:20:00.123456",
      "updated_at": "2025-07-13T10:20:00.123456"
    }
  ]
}
```

## 🚀 Quick Start

### **1. Run the File-Based Demo**
```bash
# Test the core functionality
python test_memento_files.py

# See a comprehensive demo
python demo_memento_files.py
```

### **2. Start the MCP Server**
```bash
# Terminal 1: Start the file-based server
python memento_server_files.py
```

### **3. Run the Interactive Client**
```bash
# Terminal 2: Start the file-based client
python memento_client_files.py
```

### **4. Try Natural Language Commands**
```
👤 You: Hey Memento, remember that my dentist appointment is next Tuesday at 2 PM

🧠 Memento: I've stored your dentist appointment for next Tuesday at 2 PM. 
I categorized it as a personal memory and marked it as important!

👤 You: What did I tell you about appointments?

🧠 Memento: I found 1 memory about appointments:
- Dentist appointment next Tuesday at 2 PM (stored just now)
```

## 🔧 Components

### **1. File-Based Server (`memento_server_files.py`)**
- **MCP tools** for memory operations
- **File manager** for atomic JSON operations
- **Natural language parser** for command understanding
- **User file isolation** and security

### **2. Interactive Client (`memento_client_files.py`)**
- **Azure OpenAI integration** for conversational interface
- **MCP client** for tool communication
- **Menu-driven interface** for exploration
- **Automatic user identification**

### **3. File Manager (`MementoFileManager`)**
- **Atomic file operations** with locking
- **Safe filename generation** from user IDs
- **JSON serialization** with proper encoding
- **Search and filtering** across memories

### **4. Natural Language Parser (`MementoParser`)**
- **Command classification** (store vs. recall)
- **Parameter extraction** (category, tags, importance)
- **Time period parsing** (last week, this month)
- **Content cleaning** and normalization

## 📊 Available Tools

### **`store_memory`**
Store a new memory with natural language parsing.

**Parameters:**
- `user_id` (string): Unique user identifier
- `text` (string): Memory content or natural language command
- `category` (string, optional): Memory category
- `tags` (array, optional): Memory tags
- `importance` (integer, optional): Importance level (1-10)

**Example:**
```json
{
  "user_id": "alice@laptop",
  "text": "Hey Memento, remember my dog's name is Buddy #pets #important"
}
```

### **`recall_memories`**
Search and retrieve memories with filters.

**Parameters:**
- `user_id` (string): Unique user identifier
- `query` (string): Search text or natural language query
- `category` (string, optional): Category filter
- `days_back` (integer, optional): Time filter in days
- `limit` (integer, optional): Maximum results (default: 10)

**Example:**
```json
{
  "user_id": "alice@laptop",
  "query": "What did I store about work last week?"
}
```

### **`get_memory_summary`**
Get statistics about a user's memories.

**Parameters:**
- `user_id` (string): Unique user identifier

**Returns:**
- Total memory count
- Category breakdown
- Recent activity
- File path information

### **`parse_memory_command`**
Parse natural language commands for testing.

**Parameters:**
- `text` (string): Natural language command
- `command_type` (string): "store" or "recall"

### **`list_memory_users`**
List all users with memory files (admin tool).

## 🔒 Security Features

### **1. File Path Security**
```python
def sanitize_user_id(self, user_id: str) -> str:
    """Convert user_id to a safe filename."""
    # Replace unsafe characters with underscores
    safe_chars = re.sub(r'[^\w\-@.]', '_', user_id)
    # Create a hash to ensure uniqueness and limit length
    user_hash = hashlib.md5(user_id.encode()).hexdigest()[:8]
    return f"{safe_chars}_{user_hash}"
```

**Protection against:**
- Path traversal attacks (`../../../etc/passwd`)
- Special characters in filenames
- File name conflicts
- Overly long filenames

### **2. Atomic File Operations**
```python
# Atomic write: write to temp file first, then rename
with tempfile.NamedTemporaryFile(mode='w', dir=self.memories_dir, delete=False) as temp_file:
    fcntl.flock(temp_file.fileno(), fcntl.LOCK_EX)  # Exclusive lock
    json.dump(data, temp_file, indent=2, ensure_ascii=False)
    temp_file_path = temp_file.name

# Atomic rename
shutil.move(temp_file_path, user_file)
```

**Benefits:**
- No partial writes or corruption
- Concurrent access protection
- Rollback on failure

### **3. User Data Isolation**
- Each user gets a separate file
- Server validates user_id for all operations
- No cross-user data access possible
- File permissions managed by server

## 🎯 Natural Language Examples

### **Storage Commands**
```
✅ "Hey Memento, remember that my dentist appointment is next Tuesday at 2 PM"
✅ "Store this important work task: Review Q4 budget #work #urgent"
✅ "Remember my friend's phone number is 555-1234 #contact"
✅ "I need to remember to call mom this weekend #family"
✅ "Store this idea: Use file-based storage for better isolation #ideas #tech"
```

### **Recall Commands**
```
✅ "What did I store about work last week?"
✅ "Show me personal memories from this month"
✅ "Find anything about dentist appointments"
✅ "What memories do I have about family?"
✅ "Tell me about ideas I stored recently"
```

### **Time-Based Queries**
```
✅ "Show me memories from today"
✅ "What did I store yesterday?"
✅ "Memories from this week"
✅ "What about last month?"
✅ "All memories from this year"
```

## 🔧 Deployment Considerations

### **File System Requirements**
- Writable directory for memory files
- Sufficient disk space for JSON storage
- File locking support (Unix/Linux recommended)
- Backup strategy for user files

### **Scaling Patterns**
- **Horizontal scaling**: Multiple server instances with shared file storage
- **File partitioning**: Distribute users across multiple directories
- **Backup strategies**: Regular file backups and versioning
- **Monitoring**: File size limits and disk usage alerts

### **Performance Optimization**
- **File caching**: Keep frequently accessed files in memory
- **Lazy loading**: Load user files only when needed
- **Compression**: Use compressed JSON for large memory collections
- **Indexing**: External search indexes for large datasets

## 🆚 Comparison: Files vs. Database

| Feature | File-Based | SQLite Database |
|---------|------------|-----------------|
| **Setup** | No dependencies | Requires SQLite |
| **User Isolation** | Perfect (separate files) | Good (user_id filter) |
| **Backup** | Copy individual files | Database dump |
| **Scaling** | File system limits | Database limits |
| **Concurrency** | File locking | Database transactions |
| **Search** | In-memory filtering | SQL queries |
| **Deployment** | Simple (just files) | Database management |
| **Debugging** | Easy (read JSON files) | SQL queries needed |

## 🧪 Testing

### **Run Comprehensive Tests**
```bash
# Test all functionality
python test_memento_files.py

# Expected output:
# ✅ Each user has separate files
# ✅ User data isolation verified
# ✅ Search functionality verified
# ✅ Summary functionality verified
# ✅ Natural language parsing verified
# ✅ File content structure verified
# ✅ User listing verified
# ✅ File security verified
# 🎉 All tests passed!
```

### **Run Interactive Demo**
```bash
# See the system in action
python demo_memento_files.py

# Shows:
# - User memory storage
# - File system organization
# - Search capabilities
# - Data isolation
# - Natural language parsing
```

## 🚀 Production Deployment

### **Docker Setup**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application files
COPY memento_server_files.py .
COPY memento_client_files.py .

# Create memory storage directory
RUN mkdir -p /app/memento_memories
VOLUME ["/app/memento_memories"]

# Run the server
CMD ["python", "memento_server_files.py"]
```

### **File Backup Strategy**
```bash
#!/bin/bash
# backup_memories.sh

BACKUP_DIR="/backup/memento"
MEMORY_DIR="/app/memento_memories"

# Create timestamped backup
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR/$DATE"

# Copy all user files
cp "$MEMORY_DIR"/*.json "$BACKUP_DIR/$DATE/"

# Keep only last 30 days of backups
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} \;
```

## 🎉 Key Advantages of File-Based Storage

### **1. Simplicity**
- No database setup or management
- Easy to understand and debug
- Simple backup and restore (copy files)

### **2. Perfect User Isolation**
- Physical file separation
- No chance of cross-user data leakage
- Easy to audit per-user data

### **3. Portability**
- Self-contained JSON files
- Platform independent
- Easy migration between systems

### **4. Transparency**
- Human-readable JSON format
- Easy to inspect and verify data
- Simple data export/import

### **5. Scalability**
- Distribute files across multiple storage systems
- Easy to implement sharding by user
- Independent user file management

The file-based Memento system provides a robust, secure, and simple alternative to database storage while maintaining all the intelligent memory management features! 🧠📁✨
