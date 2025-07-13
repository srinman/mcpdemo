# Memento: AI Memory System - Technical Explanation

This document provides a comprehensive technical explanation of the Memento AI Memory system, including architecture, implementation details, and learning insights.

## 🎯 System Overview

Memento is a **Model Context Protocol (MCP) based memory management system** that allows AI assistants to store and retrieve user memories using natural language commands. It demonstrates advanced MCP patterns including:

- **User data separation** and security
- **Natural language processing** for memory commands  
- **Intelligent categorization** and search
- **Azure OpenAI integration** for conversational interface
- **Persistent storage** with SQLite database

## 🏗️ Architecture Deep Dive

### **Component Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌──────────────────┐                   │
│  │                 │    │                  │                   │
│  │   Azure OpenAI  │◄──►│  Memento Client  │                   │
│  │    (GPT-4o)     │    │ (memento_client) │                   │
│  │                 │    │                  │                   │
│  └─────────────────┘    └──────────────────┘                   │
│                                │                                │
├────────────────────────────────┼────────────────────────────────┤
│                   MCP Protocol │                                │
├────────────────────────────────┼────────────────────────────────┤
│                                ▼                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Memento Server (MCP)                       │   │
│  │              (memento_server.py)                        │   │
│  │                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│  │  │store_memory │  │recall_memory│  │get_summary  │     │   │
│  │  │    tool     │  │    tool     │  │    tool     │     │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│  │                                                         │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │         Memory Database Manager                 │   │   │
│  │  │        (MementoMemoryDB class)                  │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                │                                │
├────────────────────────────────┼────────────────────────────────┤
│                  Database Layer │                                │
├────────────────────────────────┼────────────────────────────────┤
│                                ▼                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                SQLite Database                          │   │
│  │           (memento_memories.db)                         │   │
│  │                                                         │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │                memories table                   │   │   │
│  │  │  • id (PRIMARY KEY)                             │   │   │
│  │  │  • user_id (INDEXED)                            │   │   │
│  │  │  • content (TEXT)                               │   │   │
│  │  │  • category (INDEXED)                           │   │   │
│  │  │  • tags (JSON)                                  │   │   │
│  │  │  • created_at (INDEXED)                         │   │   │
│  │  │  • importance (1-10)                            │   │   │
│  │  │  • metadata (JSON)                              │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### **Data Flow Architecture**

```
1. User Input → Natural Language Command
           ↓
2. Azure OpenAI → Intent Understanding & Tool Selection  
           ↓
3. MCP Client → Tool Call to Memento Server
           ↓
4. Memento Server → Database Operation (Store/Retrieve)
           ↓
5. Database Response → Structured Memory Data
           ↓
6. MCP Response → Tool Result to Client
           ↓
7. Azure OpenAI → Natural Language Response Generation
           ↓
8. User Response → Conversational Memory Management
```

## 🔧 Implementation Details

### **1. User Identification and Data Separation**

The system implements secure user data separation without requiring OAuth:

```python
def generate_user_id(self) -> str:
    """Generate a unique user ID based on system info"""
    import getpass
    import platform
    
    username = getpass.getuser()     # System username
    hostname = platform.node()       # Machine hostname
    return f"{username}@{hostname}"   # Unique combination
```

**Security Benefits:**
- Each user gets isolated memory storage
- No cross-user data access possible  
- Simple but effective identification
- No external authentication required

**Database Implementation:**
```sql
-- All queries include user_id filter
SELECT * FROM memories WHERE user_id = ? AND category = ?

-- Indexes ensure fast user-specific queries
CREATE INDEX idx_user_id ON memories(user_id);
```

### **2. Natural Language Command Processing**

The system uses a **two-phase natural language processing** approach:

#### **Phase 1: Intent Detection**
```python
def parse_memory_command(user_input: str) -> dict:
    """Parse natural language to identify memory commands"""
    
    # Storage triggers
    store_triggers = [
        "hey memento", "remember that", "store this",
        "i want you to remember", "don't forget"
    ]
    
    # Recall triggers  
    recall_triggers = [
        "what did i tell you", "what memories", "show me",
        "what do you remember", "tell me about"
    ]
    
    # Detect intent and extract parameters
    if any(trigger in input_lower for trigger in store_triggers):
        return extract_storage_parameters(user_input)
    elif any(trigger in input_lower for trigger in recall_triggers):
        return extract_recall_parameters(user_input)
```

#### **Phase 2: Parameter Extraction**
```python
def extract_storage_parameters(user_input: str) -> dict:
    """Extract memory storage parameters from natural language"""
    
    # Content extraction (remove trigger phrases)
    content = extract_content_after_trigger(user_input)
    
    # Category detection (keyword-based)
    category = detect_category(user_input)  # work, personal, ideas, tasks
    
    # Importance detection (keyword-based)
    importance = detect_importance(user_input)  # 1-10 scale
    
    return {
        "intent": "store_memory",
        "content": content,
        "category": category, 
        "importance": importance
    }
```

### **3. Intelligent Memory Storage**

#### **Database Schema Design**
```sql
CREATE TABLE memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,              -- User separation
    content TEXT NOT NULL,              -- Memory content
    category TEXT,                      -- Auto-categorized
    tags TEXT,                          -- JSON array for search
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Time-based queries
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    importance INTEGER DEFAULT 5,       -- Priority level
    metadata TEXT                       -- Extensible JSON data
);

-- Performance indexes
CREATE INDEX idx_user_id ON memories(user_id);
CREATE INDEX idx_created_at ON memories(created_at);
CREATE INDEX idx_category ON memories(category);
```

#### **Smart Categorization Logic**
```python
def detect_category(user_input: str) -> str:
    """Automatically categorize memories based on content"""
    input_lower = user_input.lower()
    
    if any(word in input_lower for word in ["work", "job", "meeting", "project"]):
        return "work"
    elif any(word in input_lower for word in ["family", "personal", "friend"]):
        return "personal"  
    elif any(word in input_lower for word in ["idea", "thought", "inspiration"]):
        return "ideas"
    elif any(word in input_lower for word in ["task", "todo", "reminder"]):
        return "tasks"
    else:
        return "general"
```

### **4. Advanced Search and Retrieval**

#### **Multi-dimensional Search**
```python
def search_memories(self, user_id: str, query: str = None, 
                   category: str = None, days_back: int = None) -> List[Dict]:
    """Advanced memory search with multiple filters"""
    
    # Base query with user isolation
    sql = "SELECT * FROM memories WHERE user_id = ?"
    params = [user_id]
    
    # Category filtering
    if category:
        sql += " AND category = ?"
        params.append(category)
    
    # Time-based filtering
    if days_back:
        cutoff_date = datetime.now() - timedelta(days=days_back)
        sql += " AND created_at >= ?"
        params.append(cutoff_date.isoformat())
    
    # Full-text search
    if query:
        sql += " AND (content LIKE ? OR tags LIKE ?)"
        query_pattern = f"%{query}%"
        params.extend([query_pattern, query_pattern])
    
    # Sort by relevance (recent + importance)
    sql += " ORDER BY created_at DESC, importance DESC"
    
    return execute_query_and_format_results(sql, params)
```

#### **Time-based Query Processing**
```python
def parse_time_queries(user_input: str) -> int:
    """Convert natural language time references to days"""
    
    time_patterns = {
        "today": 1,
        "yesterday": 2, 
        "this week": 7,
        "last week": 14,
        "this month": 30,
        "last month": 60,
        "this year": 365
    }
    
    input_lower = user_input.lower()
    for time_phrase, days in time_patterns.items():
        if time_phrase in input_lower:
            return days
    
    return None  # No time filter
```

### **5. Azure OpenAI Integration Patterns**

#### **Tool Definition Creation**
```python
def create_memento_tool_definitions(self):
    """Convert MCP tools to Azure OpenAI function format"""
    
    tool_definitions = []
    for tool in self.available_tools:
        # MCP tool → OpenAI function definition
        tool_def = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema  # Direct mapping
            }
        }
        tool_definitions.append(tool_def)
    
    return tool_definitions
```

#### **Conversational Memory Management**
```python
async def process_memory_command(self, user_input: str):
    """Two-phase conversational memory processing"""
    
    # Phase 1: Azure OpenAI determines intent and tools needed
    response = self.azure_client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=build_conversation_context(user_input),
        tools=self.create_memento_tool_definitions(),
        tool_choice="auto"
    )
    
    # Phase 2: Execute memory tools and generate natural response
    if response.choices[0].message.tool_calls:
        # Execute MCP tools
        tool_results = await self.execute_memory_tools(response.choices[0].message.tool_calls)
        
        # Generate natural language response
        final_response = self.azure_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=build_context_with_tool_results(tool_results)
        )
        
        return final_response.choices[0].message.content
```

## 🔐 Security and Privacy Implementation

### **1. User Data Isolation**
```python
# Every database operation includes user_id filtering
def store_memory(self, user_id: str, content: str, **kwargs):
    cursor.execute('''
        INSERT INTO memories (user_id, content, category, tags, importance)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, content, category, tags_json, importance))

def search_memories(self, user_id: str, **filters):
    # User isolation at database level
    sql = "SELECT * FROM memories WHERE user_id = ?"
    params = [user_id]
    # ... additional filters
```

### **2. Input Validation and Sanitization**
```python
def validate_memory_input(self, content: str) -> bool:
    """Validate memory content before storage"""
    
    if not content or not content.strip():
        return False, "Memory content cannot be empty"
    
    if len(content) > 10000:  # Reasonable limit
        return False, "Memory content too long"
    
    # Prevent potential injection attacks
    dangerous_patterns = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'eval\s*\(',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return False, "Content contains potentially dangerous elements"
    
    return True, "Valid content"
```

### **3. Database Security**
```python
# Use parameterized queries to prevent SQL injection
cursor.execute("SELECT * FROM memories WHERE user_id = ? AND content LIKE ?", 
               (user_id, f"%{search_term}%"))

# Not: f"SELECT * FROM memories WHERE user_id = '{user_id}'"  # DANGEROUS!
```

## 🚀 Performance Optimization

### **1. Database Indexing Strategy**
```sql
-- Primary indexes for common query patterns
CREATE INDEX idx_user_id ON memories(user_id);           -- User isolation
CREATE INDEX idx_created_at ON memories(created_at);     -- Time-based queries  
CREATE INDEX idx_category ON memories(category);         -- Category filtering

-- Composite index for common combinations
CREATE INDEX idx_user_category ON memories(user_id, category);
CREATE INDEX idx_user_time ON memories(user_id, created_at);
```

### **2. Query Optimization**
```python
def search_memories_optimized(self, user_id: str, **filters):
    """Optimized memory search with result limiting"""
    
    # Use LIMIT to prevent large result sets
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(filters.get('limit', 50))
    
    # Use specific indexes based on query pattern
    if filters.get('category') and filters.get('days_back'):
        # Use composite index: idx_user_category
        sql = "SELECT * FROM memories WHERE user_id = ? AND category = ? AND created_at >= ?"
    elif filters.get('days_back'):
        # Use time index: idx_user_time  
        sql = "SELECT * FROM memories WHERE user_id = ? AND created_at >= ?"
```

### **3. Memory Management**
```python
def manage_conversation_history(self, max_length: int = 20):
    """Prevent memory leaks in long conversations"""
    
    if len(self.conversation_history) > max_length:
        # Keep recent messages only
        self.conversation_history = self.conversation_history[-max_length:]
```

## 🎯 Advanced Features Implementation

### **1. Memory Statistics and Analytics**
```python
def get_memory_stats(self, user_id: str) -> Dict:
    """Generate comprehensive memory statistics"""
    
    # Total memory count
    total_query = "SELECT COUNT(*) FROM memories WHERE user_id = ?"
    total_memories = cursor.execute(total_query, (user_id,)).fetchone()[0]
    
    # Category distribution
    category_query = '''
        SELECT category, COUNT(*) as count 
        FROM memories 
        WHERE user_id = ? 
        GROUP BY category
        ORDER BY count DESC
    '''
    categories = dict(cursor.execute(category_query, (user_id,)).fetchall())
    
    # Time-based analysis
    recent_query = '''
        SELECT COUNT(*) FROM memories 
        WHERE user_id = ? AND created_at >= ?
    '''
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    recent_memories = cursor.execute(recent_query, (user_id, week_ago)).fetchone()[0]
    
    return {
        "total_memories": total_memories,
        "categories": categories,
        "recent_memories_7_days": recent_memories,
        "average_importance": calculate_average_importance(user_id)
    }
```

### **2. Intelligent Content Processing**
```python
def extract_tags_from_content(self, content: str) -> List[str]:
    """Extract meaningful tags from memory content"""
    
    # Common important keywords
    tag_patterns = {
        'dates': r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\w+day|\w+ber \d{1,2})\b',
        'times': r'\b(\d{1,2}:\d{2}|\d{1,2} (?:AM|PM))\b',
        'people': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Proper names
        'places': r'\b(?:at|in|near) ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
    }
    
    extracted_tags = []
    for tag_type, pattern in tag_patterns.items():
        matches = re.findall(pattern, content, re.IGNORECASE)
        extracted_tags.extend(matches)
    
    return list(set(extracted_tags))  # Remove duplicates
```

### **3. Memory Importance Scoring**
```python
def calculate_importance_score(self, content: str, user_hints: str = None) -> int:
    """Calculate memory importance based on content analysis"""
    
    base_score = 5  # Default importance
    
    # High importance indicators
    high_importance_words = [
        'important', 'crucial', 'critical', 'urgent', 'deadline',
        'meeting', 'appointment', 'anniversary', 'birthday'
    ]
    
    # Low importance indicators  
    low_importance_words = [
        'maybe', 'possibly', 'minor', 'small', 'simple', 'reminder'
    ]
    
    content_lower = content.lower()
    
    # Adjust score based on keywords
    if any(word in content_lower for word in high_importance_words):
        base_score += 3
    elif any(word in content_lower for word in low_importance_words):
        base_score -= 2
    
    # Consider user hints
    if user_hints:
        hint_lower = user_hints.lower()
        if 'important' in hint_lower:
            base_score += 2
        elif 'not important' in hint_lower:
            base_score -= 2
    
    # Clamp to valid range
    return max(1, min(10, base_score))
```

## 📊 Testing and Validation

### **1. Comprehensive Test Suite**
```python
async def test_user_data_separation():
    """Verify that user data is properly isolated"""
    
    # Create memories for different users
    user1_memory = db.store_memory("user1@host", "User 1 secret")
    user2_memory = db.store_memory("user2@host", "User 2 secret")
    
    # Verify isolation
    user1_memories = db.search_memories("user1@host")
    user2_memories = db.search_memories("user2@host")
    
    assert len(user1_memories) == 1
    assert len(user2_memories) == 1
    assert user1_memories[0]['content'] != user2_memories[0]['content']
```

### **2. Natural Language Processing Tests**
```python
def test_command_parsing():
    """Test natural language command understanding"""
    
    test_cases = [
        ("Hey Memento, remember my dog's name is Buddy", "store_memory"),
        ("What did I tell you about my dog?", "recall_memories"),
        ("Show me work memories from last week", "recall_memories"),
        ("Store this: meeting at 3 PM", "store_memory")
    ]
    
    for input_text, expected_intent in test_cases:
        result = parse_memory_command(input_text)
        assert result['intent'] == expected_intent
```

### **3. Performance Testing**
```python
async def test_large_memory_dataset():
    """Test performance with large numbers of memories"""
    
    # Create 1000 memories for testing
    for i in range(1000):
        db.store_memory(
            user_id="test_user",
            content=f"Test memory #{i} with various content",
            category=random.choice(['work', 'personal', 'ideas', 'tasks'])
        )
    
    # Test search performance
    start_time = time.time()
    results = db.search_memories("test_user", query="memory", limit=50)
    search_time = time.time() - start_time
    
    assert search_time < 1.0  # Should complete within 1 second
    assert len(results) <= 50  # Respects limit
```

## 🎉 Key Learning Insights

### **1. MCP Pattern: User Context Propagation**
```python
# Always propagate user context through MCP calls
async def call_memento_tool(self, tool_name: str, arguments: dict):
    # Automatically add user context to every tool call
    arguments["user_id"] = self.user_id
    result = await self.mcp_session.call_tool(tool_name, arguments)
    return result.content[0].text
```

**Learning:** MCP tools should automatically receive user context to ensure proper data isolation without requiring users to manually specify it.

### **2. Natural Language Processing Pattern**
```python
# Two-phase NLP: Intent Detection → Parameter Extraction
def process_natural_language(user_input: str):
    # Phase 1: What does the user want to do?
    intent = detect_intent(user_input)
    
    # Phase 2: Extract specific parameters for that intent
    if intent == "store_memory":
        return extract_storage_parameters(user_input)
    elif intent == "recall_memories":
        return extract_recall_parameters(user_input)
```

**Learning:** Breaking natural language processing into phases makes it more maintainable and accurate than trying to do everything at once.

### **3. Azure OpenAI + MCP Integration Pattern**
```python
# Pattern: Azure OpenAI for understanding, MCP for execution
async def process_user_request(user_input):
    # Azure OpenAI understands intent and selects tools
    ai_response = azure_client.chat.completions.create(
        messages=[{"role": "user", "content": user_input}],
        tools=mcp_tools
    )
    
    # MCP executes the actual functionality
    for tool_call in ai_response.choices[0].message.tool_calls:
        result = await mcp_session.call_tool(tool_call.function.name, tool_call.function.arguments)
    
    # Azure OpenAI interprets results for user
    final_response = azure_client.chat.completions.create(
        messages=build_context_with_results(tool_results)
    )
```

**Learning:** The combination of Azure OpenAI for natural language understanding and MCP for structured tool execution creates powerful, conversational applications.

### **4. Database Design for MCP Applications**
```sql
-- Pattern: User-first design with performance indexes
CREATE TABLE app_data (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,      -- Always include user context
    -- ... application-specific fields
    created_at TIMESTAMP,       -- Enable time-based queries
    metadata TEXT               -- JSON for extensibility
);

-- Always index user_id for performance
CREATE INDEX idx_user_id ON app_data(user_id);
```

**Learning:** MCP applications should design their database schema with user isolation as a primary concern, using indexes to ensure good performance for user-specific queries.

## 🚀 Production Considerations

### **1. Scaling Patterns**
- **Horizontal scaling**: Multiple MCP server instances behind load balancer
- **Database sharding**: Partition users across multiple databases
- **Caching layer**: Redis for frequently accessed memories
- **Search optimization**: Full-text search engines for large datasets

### **2. Security Enhancements**
- **OAuth integration**: Replace simple user_id with proper authentication
- **Encryption**: Encrypt sensitive memory content at rest
- **Rate limiting**: Prevent abuse of memory storage
- **Audit logging**: Track all memory access for security monitoring

### **3. Feature Extensions**
- **Memory sharing**: Allow users to share specific memories
- **Memory exports**: Backup and migration capabilities
- **Advanced search**: Semantic search using embeddings
- **Memory insights**: AI-powered analysis of memory patterns

The Memento system demonstrates how MCP can be used to build sophisticated, user-centric applications that combine the power of AI understanding with structured data management! 🧠✨
