# Memento - Personal Memory Storage System

A natural language-powered memory storage system using Model Context Protocol (MCP) with Azure OpenAI integration.

## Features

🧠 **Natural Language Interface**: Use commands like "Hey memento, store this file" or "What did I save last week?"

👥 **Multi-User Support**: Complete data isolation between users with user switching capability

🔍 **Smart Search**: Search by content, time periods, tags, and descriptions

🏷️ **Tagging System**: Organize memories with custom tags for easy categorization

📊 **Analytics**: Get statistics about your stored memories

🔐 **Security**: User data is completely isolated - no cross-user access

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the `.env` file from the parent directory or create one with:

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

### 3. Start the MCP Server

```bash
python memento_mcp_server.py
```

The server will start on `http://localhost:8000/sse`

### 4. Run the Interactive Client

In a new terminal:

```bash
python memento_mcp_client_interactive.py
```

## Usage Examples

### Storing Memories

- "Hey memento, store this meeting summary about Q4 planning"
- "Save this recipe for chocolate cake with tags 'cooking,dessert'"
- "Remember this important quote for later"

### Retrieving Memories

- "What did I store last week?"
- "Find all my work-related notes"
- "Show me memories tagged with 'important'"
- "Get my notes about the project meeting"

### Managing Data

- "Show me my storage statistics"
- "List all my stored memories"
- "Delete that old note from yesterday"

## System Architecture

### Server (`memento_mcp_server.py`)

- **Storage**: Files stored in `memento_storage/{user_id}/` directories
- **Metadata**: JSON metadata files with timestamps, tags, descriptions
- **Security**: User ID sanitization and directory isolation
- **Tools**: 6 MCP tools for complete memory management

### Client (`memento_mcp_client_interactive.py`)

- **User Management**: Switch between users seamlessly
- **Azure OpenAI Integration**: Natural language processing
- **Conversation History**: Per-user conversation tracking
- **Interactive Interface**: Menu-driven system with examples

## Available Tools

| Tool | Description |
|------|-------------|
| `store_memory` | Store content with optional filename, description, and tags |
| `retrieve_memories` | Search and list memories with filtering options |
| `get_memory_content` | Get full content of a specific memory |
| `list_users` | List all users who have stored data |
| `delete_memory` | Delete a specific memory |
| `get_user_stats` | Get storage statistics for a user |

## File Structure

```
mcpmemento/
├── memento_mcp_server.py      # MCP server with storage tools
├── memento_mcp_client_interactive.py  # Interactive client
├── requirements.txt           # Python dependencies
├── README.md                 # This file
└── memento_storage/          # Auto-created storage directory
    ├── alice/               # User-specific directories
    │   ├── 20240714_143052_note.txt
    │   └── 20240714_143052_note.txt.meta
    └── bob/
        ├── 20240714_150000_recipe.txt
        └── 20240714_150000_recipe.txt.meta
```

## Security Features

- **User Isolation**: Each user's data is stored in separate directories
- **Input Sanitization**: User IDs and filenames are sanitized to prevent directory traversal
- **No Cross-User Access**: Tools verify user ownership before operations
- **Metadata Protection**: Metadata files are protected alongside content files

## Natural Language Examples

The system understands various natural language patterns:

### Storage Commands
- "store this", "save this", "remember this"
- "keep this note", "archive this content"
- "memento, store...", "hey memento..."

### Retrieval Commands
- "what did I store", "find my notes", "show me"
- "retrieve memories", "get my files"
- "what's in my storage", "search for..."

### Time-Based Queries
- "from last week", "yesterday", "today"
- "last month", "recent memories"

### Tag-Based Queries
- "tagged with work", "find work notes"
- "show me cooking recipes", "important items"

## Development

### Adding New Features

1. **Server Side**: Add new tools to `memento_mcp_server.py`
2. **Client Side**: Update tool definitions in `memento_mcp_client_interactive.py`
3. **Testing**: Use the interactive client to test new functionality

### Customization

- **Storage Location**: Modify `STORAGE_BASE_DIR` in the server
- **Default Users**: Update `self.users` list in the client
- **Tool Behavior**: Customize tool functions in the server

## Troubleshooting

### Server Won't Start
- Check if port 8000 is available
- Verify MCP library is installed: `pip install mcp`

### Client Connection Issues
- Ensure server is running first
- Check server URL in client configuration

### Azure OpenAI Issues
- Verify .env file is in parent directory
- Check API key and endpoint configuration
- Ensure deployment name is correct

### Permission Issues
- Check write permissions for storage directory
- Verify user has access to create files

## License

This project is for demonstration purposes. Adapt as needed for your use case.
