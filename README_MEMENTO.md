# Memento: AI Memory System

## 🧠 What is Memento?

**Memento: AI Memory** is an intelligent memory management system built using the Model Context Protocol (MCP). It allows AI assistants to store and retrieve user memories using natural language commands, with proper user data separation and intelligent categorization.

**Catchphrase:** *"Hey Memento"* - Your AI memory assistant

## 🎯 Key Features

### **Natural Language Memory Management**
- **Store memories** with commands like "Hey Memento, remember that..."
- **Recall memories** with queries like "What did I ask you to remember last week?"
- **Smart categorization** (work, personal, ideas, tasks, general)
- **Importance levels** (1-10 scale for prioritizing memories)

### **User Data Separation**
- Each user gets isolated memory storage
- User identification based on system username and hostname
- No cross-user data leakage

### **Intelligent Search and Retrieval**
- **Time-based queries**: "last week", "this month", "this year"
- **Category filtering**: work memories, personal memories, etc.
- **Full-text search** across memory content and tags
- **Memory statistics** and summaries

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
│                 │    │                  │    │      (MCP)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                         │
                                │                         ▼
                                │                ┌─────────────────┐
                                │                │                 │
                                │                │ SQLite Database │
                                │                │  (User Memories) │
                                │                │                 │
                                └───────────────►└─────────────────┘
                               User Commands
```

### **Components:**

1. **Memento Server (`memento_server.py`)**
   - MCP server implementing memory tools
   - SQLite database for persistent storage
   - User data isolation and security
   - Memory parsing and categorization

2. **Memento Client (`memento_client.py`)**
   - Interactive client with Azure OpenAI integration
   - Natural language command processing
   - Conversation history management
   - User-friendly interface

3. **Memory Database**
   - SQLite storage with user separation
   - Indexed for fast search and retrieval
   - Support for metadata and tags
   - Time-based filtering capabilities

## 🚀 Getting Started

### **Prerequisites**
```bash
# Install dependencies
pip install openai mcp sqlite3 python-dotenv

# Set up Azure OpenAI credentials (optional for demo)
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
export AZURE_OPENAI_API_KEY="your-api-key"  
export AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"
```

### **Running Memento**
```bash
# Start the interactive Memento client
python memento_client.py
```

The client will automatically start the MCP server and connect to it.

## 💬 Usage Examples

### **Storing Memories**
```
💭 You: Hey Memento, remember that my dentist appointment is next Tuesday at 2 PM
🧠 Memento: ✅ Memory stored successfully! I've saved your dentist appointment for next Tuesday at 2 PM in your personal memories.

💭 You: Store this work memory: The new project deadline is December 15th
🧠 Memento: ✅ Memory stored! I've categorized this as a work memory about your project deadline on December 15th.

💭 You: Don't forget that my WiFi password is SecurePass123
🧠 Memento: ✅ Remembered! I've securely stored your WiFi password information.
```

### **Recalling Memories**
```
💭 You: What did I ask you to remember about appointments?
🧠 Memento: 🧠 I found your dentist appointment scheduled for next Tuesday at 2 PM in your personal memories.

💭 You: Show me my work memories from this month
🧠 Memento: 🧠 Found 3 work memories from this month:
📝 Memory #1: The new project deadline is December 15th...

💭 You: What's my memory summary?
🧠 Memento: 📊 Memory Summary:
🗂️ Total memories: 15
📈 Recent memories (7 days): 5
📂 Categories: work (8), personal (5), ideas (2)
```

### **Natural Language Commands**

**Storage Triggers:**
- "Hey Memento, remember that..."
- "Store this memory..."
- "I want you to remember..."
- "Don't forget..."
- "Keep in mind..."

**Recall Triggers:**
- "What did I tell you..."
- "What memories do you have..."
- "Show me my... memories"
- "What do you remember about..."
- "Tell me about..."

**Time-based Queries:**
- "today", "yesterday"
- "this week", "last week"
- "this month", "last month"  
- "this year"

## 🔧 MCP Tools

### **1. store_memory**
Store a new memory for the user with categorization and metadata.

**Parameters:**
- `user_id`: User identifier (auto-added)
- `content`: Memory content to store
- `category`: Category (general, work, personal, ideas, tasks)
- `tags`: Optional tags array
- `importance`: Importance level 1-10
- `metadata`: Optional metadata object

### **2. recall_memories**
Search and retrieve stored memories based on queries.

**Parameters:**
- `user_id`: User identifier (auto-added)
- `query`: Search query text
- `category`: Filter by category
- `days_back`: Number of days to look back
- `limit`: Maximum results to return

### **3. get_memory_summary**
Get statistics and summary of user's memory storage.

**Parameters:**
- `user_id`: User identifier (auto-added)

### **4. parse_memory_command**
Parse natural language input to identify memory commands and extract parameters.

**Parameters:**
- `user_input`: Natural language input
- `user_id`: User identifier (auto-added)

## 🔐 Security and Privacy

### **User Data Separation**
- Each user gets a unique identifier: `username@hostname`
- All database queries are filtered by user_id
- No cross-user data access possible
- SQLite indexes for efficient user-specific queries

### **Data Storage**
- Local SQLite database (`memento_memories.db`)
- No external data transmission (except Azure OpenAI API)
- Structured storage with timestamps and metadata
- Easy backup and migration

### **Memory Categories**
- **general**: Default category for miscellaneous memories
- **work**: Professional and job-related memories
- **personal**: Family, friends, and personal life
- **ideas**: Creative thoughts and inspirations
- **tasks**: To-dos and reminders

## 🎯 Advanced Features

### **Smart Categorization**
The system automatically suggests categories based on content:
- Work-related keywords → "work" category
- Family/personal keywords → "personal" category
- Creative terms → "ideas" category
- Task/reminder words → "tasks" category

### **Importance Detection**
Automatic importance scoring based on language:
- **High importance (8+)**: "important", "crucial", "critical", "urgent"
- **Normal importance (5)**: Default level
- **Low importance (3-)**: "minor", "small", "simple"

### **Time-based Search**
Natural language time queries:
- "today" → memories from last 1 day
- "this week" → memories from last 7 days
- "this month" → memories from last 30 days
- "this year" → memories from last 365 days

### **Conversation Context**
- Maintains conversation history within session
- Context-aware responses based on previous interactions
- Memory continuity across multiple commands

## 🔄 Two-Phase Azure OpenAI Integration

### **Phase 1: Command Understanding**
1. User provides natural language input
2. Azure OpenAI analyzes intent and extracts parameters
3. System determines whether to store or recall memories

### **Phase 2: Memory Processing**
1. Execute appropriate MCP tools based on intent
2. Process results and provide intelligent responses
3. Update conversation context for continuity

This two-phase approach ensures intelligent, context-aware memory management that feels natural to users.

## 🎉 Why Memento is Powerful

### **1. Natural Interface**
- No complex commands or syntax to learn
- Conversational memory management
- Context-aware responses

### **2. Intelligent Organization**
- Automatic categorization and tagging
- Importance-based prioritization
- Time-based organization

### **3. Powerful Search**
- Full-text search across all memories
- Category and time-based filtering
- Natural language query understanding

### **4. User Privacy**
- Complete data separation between users
- Local storage with no external dependencies
- Secure memory management

### **5. Extensible Architecture**
- MCP-based design for easy extension
- Modular tool system
- Integration-ready with any AI system

Memento transforms how AI assistants handle user information, making memory management as natural as human conversation while maintaining privacy and intelligent organization! 🧠✨
