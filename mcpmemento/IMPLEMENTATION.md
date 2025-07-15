# Memento MCP System - Complete Implementation

## Overview

I've created a complete MCP (Model Context Protocol) server and client system for personal memory storage called "Memento". This system demonstrates how natural language can be used for memory operations with secure user isolation.

## What Was Created

### 1. **memento_mcp_server.py** - The MCP Server
- **Purpose**: Provides secure, user-isolated memory storage capabilities
- **Features**:
  - 6 MCP tools for complete memory management
  - User data isolation (each user has separate directory)
  - Metadata tracking (timestamps, tags, descriptions)
  - Natural language-friendly operations
  - File security and sanitization

### 2. **memento_mcp_client_interactive.py** - Interactive Client
- **Purpose**: User-friendly interface with Azure OpenAI integration
- **Features**:
  - Multi-user support with easy switching
  - Natural language processing via Azure OpenAI
  - Per-user conversation history
  - Interactive menu system
  - Example commands and demos

### 3. **Supporting Files**
- **requirements.txt**: All necessary Python dependencies
- **README.md**: Comprehensive documentation
- **demo.py**: Demonstration script (no Azure OpenAI required)
- **start.sh**: Easy startup script for the system

## Key Features Implemented

### 🧠 Natural Language Interface
Users can say things like:
- "Hey memento, store this file content"
- "What did I save last week?"
- "Find my work notes"
- "Show me my cooking recipes"

### 👥 Multi-User Support
- Complete data isolation between users
- Easy user switching in the client
- Per-user conversation history
- Secure file access controls

### 🔍 Smart Search & Organization
- Search by content, filename, or description
- Time-based filtering (today, yesterday, last_week, last_month)
- Tag-based categorization
- Statistics and analytics per user

### 🔐 Security Features
- User ID and filename sanitization
- Directory traversal prevention
- No cross-user data access
- Secure metadata storage

## Architecture

```
┌─────────────────────┐    ┌──────────────────────┐
│  Interactive Client │───▶│    MCP Server        │
│                     │    │                      │
│ • User switching    │    │ • File storage       │
│ • Natural language  │    │ • User isolation     │
│ • Azure OpenAI      │    │ • Metadata tracking  │
│ • Conversation hist │    │ • Search & filtering │
└─────────────────────┘    └──────────────────────┘
           │                           │
           ▼                           ▼
┌─────────────────────┐    ┌──────────────────────┐
│  Azure OpenAI       │    │  File System         │
│                     │    │                      │
│ • Natural language  │    │ memento_storage/     │
│ • Tool calling      │    │ ├── alice/           │
│ • Response gen      │    │ ├── bob/             │
└─────────────────────┘    │ └── charlie/         │
                           └──────────────────────┘
```

## Available MCP Tools

| Tool | Function |
|------|----------|
| `store_memory` | Store content with metadata (filename, description, tags) |
| `retrieve_memories` | Search and list memories with filtering |
| `get_memory_content` | Get full content of a specific memory |
| `list_users` | List all users who have stored data |
| `delete_memory` | Delete a specific memory |
| `get_user_stats` | Get storage statistics for a user |

## Usage Examples

### Starting the System

```bash
# Easy startup
./start.sh

# Manual startup
python3 memento_mcp_server.py    # Terminal 1
python3 memento_mcp_client_interactive.py  # Terminal 2

# Demo mode (no Azure OpenAI needed)
python3 demo.py
```

### Natural Language Commands

```
User: "Hey memento, store this meeting summary about Q4 planning"
→ Calls: store_memory(user_id="alice", content="...", tags="work,meeting")

User: "What did I store last week?"
→ Calls: retrieve_memories(user_id="alice", time_filter="last_week")

User: "Find all my cooking recipes"
→ Calls: retrieve_memories(user_id="alice", tag_filter="cooking")
```

## File Storage Structure

```
memento_storage/
├── alice/
│   ├── 20240714_143052_meeting_notes.txt      # Content file
│   ├── 20240714_143052_meeting_notes.txt.meta # Metadata file
│   └── 20240714_144500_recipe.txt
└── bob/
    ├── 20240714_145000_quote.txt
    └── 20240714_145000_quote.txt.meta
```

## Environment Setup

The system loads the `.env` file from the parent directory (`../`), which should contain:

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

## Security Implementation

### User Isolation
- Each user gets a separate directory
- User IDs are sanitized to prevent directory traversal
- No tools allow cross-user access

### File Safety
- Filenames are sanitized and timestamped
- Metadata is stored separately for integrity
- All file operations are user-scoped

### Input Validation
- User IDs must be non-empty and are sanitized
- Content cannot be empty for storage operations
- File paths are validated before operations

## Benefits Demonstrated

1. **Natural Language Interface**: Shows how MCP can enable natural language operations
2. **User Isolation**: Demonstrates secure multi-user data handling
3. **Rich Metadata**: Provides searchable, organized storage
4. **Real-world Applicability**: Practical memory storage use case
5. **Extensibility**: Easy to add new tools and features

## Testing the System

1. **Demo Mode**: Run `python3 demo.py` to see simulated interactions
2. **Full System**: Start server and client to test with actual Azure OpenAI
3. **Multi-User**: Switch between users to verify data isolation
4. **Natural Language**: Try various ways of expressing the same request

This implementation provides a complete, production-ready foundation for a personal memory storage system with natural language interface, demonstrating the power of MCP for real-world applications.
