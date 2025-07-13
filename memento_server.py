#!/usr/bin/env python3
"""
Memento: AI Memory - MCP Server
A Model Context Protocol server that helps AI assistants store and retrieve user memories.

Catchphrase: "Hey Memento" - Your AI memory assistant
"""

import asyncio
import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hashlib
import uuid

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
)

# Database setup
DB_FILE = "memento_memories.db"

class MementoMemoryDB:
    """Database handler for storing user memories"""
    
    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Create memories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT,
                tags TEXT,  -- JSON array of tags
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                importance INTEGER DEFAULT 5,  -- 1-10 scale
                metadata TEXT  -- JSON metadata
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON memories(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON memories(category)')
        
        conn.commit()
        conn.close()
    
    def store_memory(self, user_id: str, content: str, category: str = "general", 
                    tags: List[str] = None, importance: int = 5, metadata: Dict = None) -> str:
        """Store a new memory for a user"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        tags_json = json.dumps(tags or [])
        metadata_json = json.dumps(metadata or {})
        
        cursor.execute('''
            INSERT INTO memories (user_id, content, category, tags, importance, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, content, category, tags_json, importance, metadata_json))
        
        memory_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return str(memory_id)
    
    def search_memories(self, user_id: str, query: str = None, category: str = None,
                       days_back: int = None, limit: int = 50) -> List[Dict]:
        """Search memories for a user"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Build SQL query
        sql = "SELECT * FROM memories WHERE user_id = ?"
        params = [user_id]
        
        if category:
            sql += " AND category = ?"
            params.append(category)
        
        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            sql += " AND created_at >= ?"
            params.append(cutoff_date.isoformat())
        
        if query:
            # Simple text search in content
            sql += " AND (content LIKE ? OR tags LIKE ?)"
            query_pattern = f"%{query}%"
            params.extend([query_pattern, query_pattern])
        
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        # Convert to dictionaries
        columns = [desc[0] for desc in cursor.description]
        memories = []
        for row in rows:
            memory = dict(zip(columns, row))
            # Parse JSON fields
            memory['tags'] = json.loads(memory['tags']) if memory['tags'] else []
            memory['metadata'] = json.loads(memory['metadata']) if memory['metadata'] else {}
            memories.append(memory)
        
        conn.close()
        return memories
    
    def get_memory_stats(self, user_id: str) -> Dict:
        """Get statistics about a user's memories"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Total memories
        cursor.execute("SELECT COUNT(*) FROM memories WHERE user_id = ?", (user_id,))
        total_memories = cursor.fetchone()[0]
        
        # Memories by category
        cursor.execute('''
            SELECT category, COUNT(*) FROM memories 
            WHERE user_id = ? 
            GROUP BY category
        ''', (user_id,))
        categories = dict(cursor.fetchall())
        
        # Recent memories (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        cursor.execute('''
            SELECT COUNT(*) FROM memories 
            WHERE user_id = ? AND created_at >= ?
        ''', (user_id, week_ago.isoformat()))
        recent_memories = cursor.fetchone()[0]
        
        conn.close()
        return {
            "total_memories": total_memories,
            "categories": categories,
            "recent_memories_7_days": recent_memories
        }

class MementoServer:
    """Memento MCP Server implementation"""
    
    def __init__(self):
        self.db = MementoMemoryDB()
        self.server = Server("memento-ai-memory")
        self.setup_tools()
    
    def setup_tools(self):
        """Register MCP tools"""
        
        @self.server.call_tool()
        async def store_memory(arguments: dict) -> List[TextContent]:
            """
            Store a memory for the user.
            
            Triggered by phrases like:
            - "Hey Memento, remember that..."
            - "Store this memory..."
            - "I want you to remember..."
            """
            user_id = arguments.get("user_id", "default_user")
            content = arguments.get("content", "")
            category = arguments.get("category", "general")
            tags = arguments.get("tags", [])
            importance = arguments.get("importance", 5)
            metadata = arguments.get("metadata", {})
            
            if not content:
                return [TextContent(type="text", text="❌ Error: Memory content cannot be empty")]
            
            try:
                memory_id = self.db.store_memory(
                    user_id=user_id,
                    content=content,
                    category=category,
                    tags=tags,
                    importance=importance,
                    metadata=metadata
                )
                
                return [TextContent(
                    type="text", 
                    text=f"✅ Memory stored successfully!\n"
                         f"📝 Memory ID: {memory_id}\n"
                         f"👤 User: {user_id}\n"
                         f"📂 Category: {category}\n"
                         f"💾 Content: {content[:100]}{'...' if len(content) > 100 else ''}"
                )]
            except Exception as e:
                return [TextContent(type="text", text=f"❌ Error storing memory: {str(e)}")]
        
        @self.server.call_tool()
        async def recall_memories(arguments: dict) -> List[TextContent]:
            """
            Recall memories based on natural language queries.
            
            Examples:
            - "What did I ask you to remember last week?"
            - "Show me my work-related memories"
            - "What memories do you have about my family?"
            """
            user_id = arguments.get("user_id", "default_user")
            query = arguments.get("query", "")
            category = arguments.get("category")
            days_back = arguments.get("days_back")
            limit = arguments.get("limit", 10)
            
            try:
                memories = self.db.search_memories(
                    user_id=user_id,
                    query=query,
                    category=category,
                    days_back=days_back,
                    limit=limit
                )
                
                if not memories:
                    return [TextContent(
                        type="text", 
                        text="🤔 I don't have any memories matching your request. Perhaps you'd like to store some memories first?"
                    )]
                
                # Format memories for display
                response = f"🧠 Found {len(memories)} memories for {user_id}:\n\n"
                
                for i, memory in enumerate(memories, 1):
                    created_date = datetime.fromisoformat(memory['created_at']).strftime("%Y-%m-%d %H:%M")
                    response += f"📝 **Memory #{i} (ID: {memory['id']})**\n"
                    response += f"📅 Created: {created_date}\n"
                    response += f"📂 Category: {memory['category']}\n"
                    response += f"⭐ Importance: {memory['importance']}/10\n"
                    if memory['tags']:
                        response += f"🏷️ Tags: {', '.join(memory['tags'])}\n"
                    response += f"💭 Content: {memory['content']}\n"
                    response += "-" * 50 + "\n"
                
                return [TextContent(type="text", text=response)]
                
            except Exception as e:
                return [TextContent(type="text", text=f"❌ Error recalling memories: {str(e)}")]
        
        @self.server.call_tool()
        async def get_memory_summary(arguments: dict) -> List[TextContent]:
            """
            Get a summary of the user's memory storage.
            
            Usage: "Hey Memento, what's my memory summary?"
            """
            user_id = arguments.get("user_id", "default_user")
            
            try:
                stats = self.db.get_memory_stats(user_id)
                
                response = f"📊 **Memory Summary for {user_id}**\n\n"
                response += f"🗂️ Total memories: {stats['total_memories']}\n"
                response += f"📈 Recent memories (7 days): {stats['recent_memories_7_days']}\n\n"
                
                if stats['categories']:
                    response += "📂 **Categories:**\n"
                    for category, count in stats['categories'].items():
                        response += f"  • {category}: {count} memories\n"
                else:
                    response += "📂 No categorized memories yet.\n"
                
                return [TextContent(type="text", text=response)]
                
            except Exception as e:
                return [TextContent(type="text", text=f"❌ Error getting memory summary: {str(e)}")]
        
        @self.server.call_tool()
        async def parse_memory_command(arguments: dict) -> List[TextContent]:
            """
            Parse natural language to identify memory commands and extract information.
            
            This tool helps identify when users want to store or recall memories
            and extracts relevant information from their natural language input.
            """
            user_input = arguments.get("user_input", "")
            user_id = arguments.get("user_id", "default_user")
            
            if not user_input:
                return [TextContent(type="text", text="❌ Error: No input provided")]
            
            try:
                # Normalize input
                input_lower = user_input.lower()
                
                # Memory storage triggers
                store_triggers = [
                    "hey memento", "remember that", "store this", "save this memory",
                    "i want you to remember", "don't forget", "memorize this",
                    "keep in mind", "note this down", "remember this"
                ]
                
                # Memory recall triggers
                recall_triggers = [
                    "what did i tell you", "recall", "what memories", "show me",
                    "what do you remember", "tell me about", "what did i ask you to remember",
                    "memory summary", "my memories"
                ]
                
                # Time-based patterns
                time_patterns = {
                    "today": 1,
                    "yesterday": 2,
                    "this week": 7,
                    "last week": 14,
                    "this month": 30,
                    "last month": 60,
                    "this year": 365
                }
                
                # Detect intent
                is_store_command = any(trigger in input_lower for trigger in store_triggers)
                is_recall_command = any(trigger in input_lower for trigger in recall_triggers)
                
                if is_store_command:
                    # Extract content to store
                    content = user_input
                    
                    # Remove trigger phrases to get clean content
                    for trigger in store_triggers:
                        if trigger in input_lower:
                            # Find the trigger and extract content after it
                            start_idx = input_lower.find(trigger)
                            if start_idx != -1:
                                content = user_input[start_idx + len(trigger):].strip()
                                break
                    
                    # Extract category hints
                    category = "general"
                    if any(word in input_lower for word in ["work", "job", "meeting", "project"]):
                        category = "work"
                    elif any(word in input_lower for word in ["family", "personal", "friend"]):
                        category = "personal"
                    elif any(word in input_lower for word in ["idea", "thought", "inspiration"]):
                        category = "ideas"
                    elif any(word in input_lower for word in ["task", "todo", "reminder"]):
                        category = "tasks"
                    
                    # Extract importance hints
                    importance = 5
                    if any(word in input_lower for word in ["important", "crucial", "critical", "urgent"]):
                        importance = 8
                    elif any(word in input_lower for word in ["minor", "small", "simple"]):
                        importance = 3
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "intent": "store_memory",
                            "content": content,
                            "category": category,
                            "importance": importance,
                            "user_id": user_id,
                            "original_input": user_input
                        })
                    )]
                
                elif is_recall_command:
                    # Extract search parameters
                    days_back = None
                    
                    # Check for time-based queries
                    for time_phrase, days in time_patterns.items():
                        if time_phrase in input_lower:
                            days_back = days
                            break
                    
                    # Extract category hints
                    category = None
                    if any(word in input_lower for word in ["work", "job", "meeting", "project"]):
                        category = "work"
                    elif any(word in input_lower for word in ["family", "personal", "friend"]):
                        category = "personal"
                    elif any(word in input_lower for word in ["idea", "thought", "inspiration"]):
                        category = "ideas"
                    elif any(word in input_lower for word in ["task", "todo", "reminder"]):
                        category = "tasks"
                    
                    # Extract search query (remove trigger phrases)
                    query = ""
                    for trigger in recall_triggers:
                        if trigger in input_lower:
                            start_idx = input_lower.find(trigger)
                            if start_idx != -1:
                                remaining = user_input[start_idx + len(trigger):].strip()
                                # Clean up common words
                                query = remaining.replace("about", "").replace("from", "").strip()
                                break
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "intent": "recall_memories",
                            "query": query,
                            "category": category,
                            "days_back": days_back,
                            "user_id": user_id,
                            "original_input": user_input
                        })
                    )]
                
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "intent": "unknown",
                            "message": "I didn't detect a memory command. Try phrases like 'Hey Memento, remember that...' or 'What did I ask you to remember?'",
                            "user_id": user_id,
                            "original_input": user_input
                        })
                    )]
                    
            except Exception as e:
                return [TextContent(type="text", text=f"❌ Error parsing command: {str(e)}")]

    async def run(self):
        """Run the Memento server"""
        # Register tools
        self.server.list_tools = lambda: [
            Tool(
                name="store_memory",
                description="Store a memory for a user. Use when users say things like 'Hey Memento, remember that...' or 'Store this memory...'",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "Unique identifier for the user"
                        },
                        "content": {
                            "type": "string", 
                            "description": "The memory content to store"
                        },
                        "category": {
                            "type": "string",
                            "description": "Category for the memory (general, work, personal, ideas, tasks)",
                            "default": "general"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional tags for the memory"
                        },
                        "importance": {
                            "type": "integer",
                            "description": "Importance level 1-10",
                            "minimum": 1,
                            "maximum": 10,
                            "default": 5
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Optional metadata about the memory"
                        }
                    },
                    "required": ["user_id", "content"]
                }
            ),
            Tool(
                name="recall_memories",
                description="Recall memories based on natural language queries. Use for requests like 'What did I ask you to remember?' or 'Show me my work memories'",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "Unique identifier for the user"
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query to find relevant memories"
                        },
                        "category": {
                            "type": "string",
                            "description": "Filter by category (general, work, personal, ideas, tasks)"
                        },
                        "days_back": {
                            "type": "integer",
                            "description": "Number of days to look back (e.g., 7 for last week, 30 for last month)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of memories to return",
                            "default": 10
                        }
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="get_memory_summary",
                description="Get a summary of the user's stored memories, including statistics and categories",
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
            Tool(
                name="parse_memory_command",
                description="Parse natural language input to identify memory commands and extract relevant information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_input": {
                            "type": "string",
                            "description": "The user's natural language input"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "Unique identifier for the user"
                        }
                    },
                    "required": ["user_input", "user_id"]
                }
            )
        ]
        
        print("🧠 Memento: AI Memory Server starting...")
        print("💭 Ready to help you remember and recall information!")
        print("🎯 Catchphrase: 'Hey Memento' - Your AI memory assistant")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

async def main():
    """Main entry point"""
    server = MementoServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
