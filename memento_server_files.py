#!/usr/bin/env python3
"""
Memento: AI Memory MCP Server (File-Based Storage)

A Model Context Protocol server that provides AI-powered memory storage and retrieval
using individual JSON files for each user instead of SQLite database.

Key features:
- User-specific file isolation (no cross-user data leakage)
- JSON-based memory storage in separate files per user
- Natural language storage and retrieval
- Time-based and category-based queries
- File-based persistence with atomic operations
- Security-first design following MCP authorization best practices

Catchphrase: "Hey Memento" - Your AI memory assistant
"""

import asyncio
import json
import os
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any, Sequence, Optional, Dict, List
from pathlib import Path
import re
import tempfile
import shutil

# Cross-platform file locking
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio


# Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("memento-server-files")

# File storage configuration
MEMORIES_DIR = Path("memento_memories")
USER_FILE_EXTENSION = ".json"

class MementoFileManager:
    """Handles all file operations for the Memento memory system."""
    
    def __init__(self, memories_dir: Path = MEMORIES_DIR):
        self.memories_dir = memories_dir
        self.ensure_memories_directory()
    
    def ensure_memories_directory(self):
        """Create the memories directory if it doesn't exist."""
        self.memories_dir.mkdir(exist_ok=True)
        logger.info(f"Memories directory ensured at: {self.memories_dir}")
    
    def get_user_file_path(self, user_id: str) -> Path:
        """Get the file path for a specific user's memories."""
        # Sanitize user_id to create a safe filename
        safe_user_id = self.sanitize_user_id(user_id)
        return self.memories_dir / f"{safe_user_id}{USER_FILE_EXTENSION}"
    
    def sanitize_user_id(self, user_id: str) -> str:
        """Convert user_id to a safe filename."""
        # Replace unsafe characters with underscores
        safe_chars = re.sub(r'[^\w\-@.]', '_', user_id)
        # Create a hash to ensure uniqueness and limit length
        user_hash = hashlib.md5(user_id.encode()).hexdigest()[:8]
        return f"{safe_chars}_{user_hash}"
    
    def load_user_memories(self, user_id: str) -> List[Dict]:
        """Load all memories for a specific user from their file."""
        user_file = self.get_user_file_path(user_id)
        
        if not user_file.exists():
            return []
        
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                # Use file locking if available (Unix/Linux)
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock for reading
                data = json.load(f)
                return data.get('memories', [])
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading memories for user {user_id}: {e}")
            return []
    
    def save_user_memories(self, user_id: str, memories: List[Dict]) -> bool:
        """Save all memories for a specific user to their file."""
        user_file = self.get_user_file_path(user_id)
        
        # Prepare data structure
        data = {
            'user_id': user_id,
            'last_updated': datetime.now().isoformat(),
            'total_memories': len(memories),
            'memories': memories
        }
        
        try:
            # Atomic write: write to temp file first, then rename
            with tempfile.NamedTemporaryFile(
                mode='w', 
                encoding='utf-8', 
                dir=self.memories_dir, 
                delete=False
            ) as temp_file:
                # Use file locking if available (Unix/Linux)
                if HAS_FCNTL:
                    fcntl.flock(temp_file.fileno(), fcntl.LOCK_EX)  # Exclusive lock for writing
                json.dump(data, temp_file, indent=2, ensure_ascii=False)
                temp_file_path = temp_file.name
            
            # Atomic rename
            shutil.move(temp_file_path, user_file)
            logger.info(f"Saved {len(memories)} memories for user {user_id}")
            return True
            
        except (IOError, OSError) as e:
            logger.error(f"Error saving memories for user {user_id}: {e}")
            # Clean up temp file if it exists
            if 'temp_file_path' in locals() and Path(temp_file_path).exists():
                Path(temp_file_path).unlink()
            return False
    
    def store_memory(self, user_id: str, content: str, category: str = None, 
                    tags: List[str] = None, importance: int = 5, metadata: Dict = None) -> int:
        """Store a new memory for a specific user."""
        # Load existing memories
        memories = self.load_user_memories(user_id)
        
        # Generate new memory ID (simple incrementing ID based on existing memories)
        memory_id = max([m.get('id', 0) for m in memories], default=0) + 1
        
        # Create new memory entry
        new_memory = {
            'id': memory_id,
            'content': content,
            'category': category or 'general',
            'tags': tags or [],
            'importance': importance,
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Add to memories list
        memories.append(new_memory)
        
        # Save back to file
        if self.save_user_memories(user_id, memories):
            logger.info(f"Stored memory {memory_id} for user {user_id}")
            return memory_id
        else:
            raise Exception(f"Failed to store memory for user {user_id}")
    
    def search_memories(self, user_id: str, query: str = None, category: str = None,
                       days_back: int = None, limit: int = 50) -> List[Dict]:
        """Search memories for a specific user with various filters."""
        memories = self.load_user_memories(user_id)
        
        filtered_memories = []
        
        for memory in memories:
            # Apply filters
            if category and memory.get('category') != category:
                continue
            
            if days_back:
                memory_date = datetime.fromisoformat(memory['created_at'])
                cutoff_date = datetime.now() - timedelta(days=days_back)
                if memory_date < cutoff_date:
                    continue
            
            if query:
                # Search in content, category, and tags
                search_text = query.lower()
                content_match = search_text in memory.get('content', '').lower()
                category_match = search_text in memory.get('category', '').lower()
                tags_match = any(search_text in tag.lower() for tag in memory.get('tags', []))
                
                if not (content_match or category_match or tags_match):
                    continue
            
            filtered_memories.append(memory)
        
        # Sort by creation date (newest first) and importance (highest first)
        filtered_memories.sort(
            key=lambda m: (
                datetime.fromisoformat(m['created_at']), 
                m.get('importance', 5)
            ), 
            reverse=True
        )
        
        # Apply limit
        result = filtered_memories[:limit]
        
        logger.info(f"Found {len(result)} memories for user {user_id}")
        return result
    
    def get_memory_summary(self, user_id: str) -> Dict:
        """Get a summary of all memories for a user."""
        memories = self.load_user_memories(user_id)
        
        if not memories:
            return {
                "total_memories": 0,
                "categories": {},
                "recent_memories": 0,
                "user_id": user_id,
                "file_path": str(self.get_user_file_path(user_id))
            }
        
        # Count by category
        categories = {}
        for memory in memories:
            category = memory.get('category', 'general')
            categories[category] = categories.get(category, 0) + 1
        
        # Count recent memories (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_memories = 0
        for memory in memories:
            memory_date = datetime.fromisoformat(memory['created_at'])
            if memory_date >= week_ago:
                recent_memories += 1
        
        return {
            "total_memories": len(memories),
            "categories": categories,
            "recent_memories": recent_memories,
            "user_id": user_id,
            "file_path": str(self.get_user_file_path(user_id))
        }
    
    def list_all_users(self) -> List[str]:
        """Get a list of all users who have memory files."""
        users = []
        for file_path in self.memories_dir.glob(f"*{USER_FILE_EXTENSION}"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'user_id' in data:
                        users.append(data['user_id'])
            except (json.JSONDecodeError, IOError):
                continue
        return users


class MementoParser:
    """Parses natural language commands for memory operations."""
    
    @staticmethod
    def parse_store_command(text: str) -> Dict:
        """Parse a memory storage command and extract content, category, and tags."""
        # Remove trigger phrases
        triggers = ["hey memento", "memento", "remember", "store", "save"]
        clean_text = text.lower()
        for trigger in triggers:
            clean_text = re.sub(rf'\b{trigger}\b', '', clean_text, flags=re.IGNORECASE)
        clean_text = clean_text.strip()
        
        # Extract category hints
        category_patterns = {
            "work": r'\b(work|job|meeting|project|task|deadline|office)\b',
            "personal": r'\b(personal|family|friend|home|private)\b',
            "ideas": r'\b(idea|thought|concept|brainstorm|inspiration)\b',
            "tasks": r'\b(todo|task|reminder|do|complete|finish)\b',
            "notes": r'\b(note|jot|write down|record|remember)\b',
            "contacts": r'\b(contact|person|phone|email|address)\b',
            "events": r'\b(meeting|event|appointment|conference|call)\b'
        }
        
        detected_category = None
        for category, pattern in category_patterns.items():
            if re.search(pattern, clean_text, re.IGNORECASE):
                detected_category = category
                break
        
        # Extract hashtags as tags
        tags = re.findall(r'#(\w+)', text)
        
        # Extract importance hints
        importance = 5  # default
        if re.search(r'\b(important|urgent|critical|crucial)\b', clean_text, re.IGNORECASE):
            importance = 8
        elif re.search(r'\b(minor|small|simple|low)\b', clean_text, re.IGNORECASE):
            importance = 3
        
        # The main content is what remains
        content = re.sub(r'#\w+', '', clean_text).strip()
        content = re.sub(r'\b(important|urgent|critical|crucial|minor|small|simple|low)\b', '', content, flags=re.IGNORECASE).strip()
        
        return {
            "content": content,
            "category": detected_category,
            "tags": tags,
            "importance": importance
        }
    
    @staticmethod
    def parse_recall_command(text: str) -> Dict:
        """Parse a memory recall command and extract search parameters."""
        clean_text = text.lower()
        
        # Remove trigger phrases
        triggers = ["hey memento", "memento", "recall", "remember", "what", "find", "search", "show me"]
        for trigger in triggers:
            clean_text = re.sub(rf'\b{trigger}\b', '', clean_text, flags=re.IGNORECASE)
        clean_text = clean_text.strip()
        
        # Extract time-based filters
        time_patterns = {
            "today": r'\btoday\b',
            "yesterday": r'\byesterday\b',
            "this week": r'\bthis week\b',
            "last week": r'\blast week\b',
            "this month": r'\bthis month\b',
            "last month": r'\blast month\b',
            "this year": r'\bthis year\b'
        }
        
        days_back = None
        for period, pattern in time_patterns.items():
            if re.search(pattern, clean_text):
                if "today" in period:
                    days_back = 1
                elif "yesterday" in period:
                    days_back = 2
                elif "week" in period:
                    days_back = 7 if "this" in period else 14
                elif "month" in period:
                    days_back = 30 if "this" in period else 60
                elif "year" in period:
                    days_back = 365
                break
        
        # Extract category hints
        category_patterns = {
            "work": r'\b(work|job|meeting|project)\b',
            "personal": r'\b(personal|family|friend)\b',
            "ideas": r'\b(idea|ideas|thought|thoughts)\b',
            "tasks": r'\b(task|tasks|todo|reminder)\b',
            "notes": r'\b(note|notes)\b',
            "contacts": r'\b(contact|contacts|person|people)\b',
            "events": r'\b(meeting|meetings|event|events|appointment)\b'
        }
        
        detected_category = None
        for category, pattern in category_patterns.items():
            if re.search(pattern, clean_text, re.IGNORECASE):
                detected_category = category
                break
        
        # Extract search query (remove time and category words)
        query_text = clean_text
        for pattern in time_patterns.values():
            query_text = re.sub(pattern, '', query_text)
        for pattern in category_patterns.values():
            query_text = re.sub(pattern, '', query_text)
        
        query_text = re.sub(r'\b(did i|about|from|for|with|all|my)\b', '', query_text).strip()
        
        return {
            "query": query_text if query_text else None,
            "category": detected_category,
            "days_back": days_back
        }


# Initialize the server
server = Server("memento-server-files")
file_manager = MementoFileManager()
parser = MementoParser()

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools for the Memento memory system."""
    return [
        types.Tool(
            name="store_memory",
            description="Store a memory with content, optional category, and tags. Supports natural language input. Uses file-based storage with per-user files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Unique identifier for the user (ensures data separation in individual files)"
                    },
                    "text": {
                        "type": "string",
                        "description": "The memory content or natural language command to store"
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category for the memory (auto-detected if not provided)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional tags for the memory (auto-extracted from #hashtags if not provided)"
                    },
                    "importance": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "description": "Importance level from 1-10 (auto-detected if not provided)"
                    }
                },
                "required": ["user_id", "text"]
            }
        ),
        types.Tool(
            name="recall_memories",
            description="Search and recall memories using natural language queries, with support for time-based and category-based filtering. Searches within user's individual file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Unique identifier for the user (ensures data separation)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Natural language query or search text"
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category filter"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Optional number of days to look back"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of memories to return (default: 10)"
                    }
                },
                "required": ["user_id", "query"]
            }
        ),
        types.Tool(
            name="get_memory_summary",
            description="Get a summary of all stored memories for a user, including counts by category and recent activity. Reads from user's individual file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Unique identifier for the user"
                    }
                },
                "required": ["user_id"]
            }
        ),
        types.Tool(
            name="parse_memory_command",
            description="Parse a natural language command to understand memory storage or recall intent.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Natural language command to parse"
                    },
                    "command_type": {
                        "type": "string",
                        "enum": ["store", "recall"],
                        "description": "Type of command to parse"
                    }
                },
                "required": ["text", "command_type"]
            }
        ),
        types.Tool(
            name="list_memory_users",
            description="List all users who have stored memories in the file-based system. Admin/debug tool.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls for memory operations."""
    
    if name == "store_memory":
        user_id = arguments["user_id"]
        text = arguments["text"]
        
        # Parse the text to extract structured information
        parsed = parser.parse_store_command(text)
        
        # Use provided arguments or parsed values
        category = arguments.get("category", parsed["category"])
        tags = arguments.get("tags", parsed["tags"])
        importance = arguments.get("importance", parsed["importance"])
        content = parsed["content"] if parsed["content"] else text
        
        # Store the memory
        memory_id = file_manager.store_memory(
            user_id=user_id,
            content=content,
            category=category,
            tags=tags,
            importance=importance
        )
        
        result = {
            "success": True,
            "memory_id": memory_id,
            "content": content,
            "category": category,
            "tags": tags,
            "importance": importance,
            "storage_type": "file-based",
            "user_file": str(file_manager.get_user_file_path(user_id)),
            "message": f"Memory stored successfully with ID {memory_id} in user file"
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "recall_memories":
        user_id = arguments["user_id"]
        query_text = arguments["query"]
        
        # Parse the query to extract search parameters
        parsed = parser.parse_recall_command(query_text)
        
        # Use provided arguments or parsed values
        category = arguments.get("category", parsed["category"])
        days_back = arguments.get("days_back", parsed["days_back"])
        limit = arguments.get("limit", 10)
        search_query = parsed["query"]
        
        # Search memories
        memories = file_manager.search_memories(
            user_id=user_id,
            query=search_query,
            category=category,
            days_back=days_back,
            limit=limit
        )
        
        result = {
            "success": True,
            "query": {
                "text": query_text,
                "parsed_query": search_query,
                "category": category,
                "days_back": days_back
            },
            "memories": memories,
            "count": len(memories),
            "storage_type": "file-based",
            "user_file": str(file_manager.get_user_file_path(user_id))
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "get_memory_summary":
        user_id = arguments["user_id"]
        summary = file_manager.get_memory_summary(user_id)
        summary["storage_type"] = "file-based"
        
        return [types.TextContent(
            type="text",
            text=json.dumps(summary, indent=2)
        )]
    
    elif name == "parse_memory_command":
        text = arguments["text"]
        command_type = arguments["command_type"]
        
        if command_type == "store":
            parsed = parser.parse_store_command(text)
        elif command_type == "recall":
            parsed = parser.parse_recall_command(text)
        else:
            raise ValueError(f"Unknown command type: {command_type}")
        
        result = {
            "command_type": command_type,
            "original_text": text,
            "parsed": parsed,
            "storage_type": "file-based"
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "list_memory_users":
        users = file_manager.list_all_users()
        
        result = {
            "users": users,
            "user_count": len(users),
            "storage_type": "file-based",
            "storage_directory": str(file_manager.memories_dir)
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main entry point for the Memento MCP server."""
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="memento-files",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
