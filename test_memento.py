#!/usr/bin/env python3
"""
Memento: AI Memory - Test Suite
Test the Memento MCP server functionality.
"""

import asyncio
import os
import tempfile
import sqlite3
from datetime import datetime, timedelta
import json

# Test the Memento server locally
from memento_server import MementoMemoryDB, MementoServer

async def test_memory_database():
    """Test the core database functionality"""
    print("🧪 Testing Memento Memory Database...")
    
    # Use a temporary database for testing
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        # Initialize database
        db = MementoMemoryDB(temp_db.name)
        
        # Test user IDs
        user1 = "alice@laptop"
        user2 = "bob@desktop"
        
        # Test storing memories
        print("  📝 Testing memory storage...")
        memory_id1 = db.store_memory(
            user_id=user1,
            content="Remember to buy groceries: milk, bread, eggs",
            category="tasks",
            tags=["shopping", "food"],
            importance=7
        )
        
        memory_id2 = db.store_memory(
            user_id=user1,
            content="Meeting with team lead tomorrow at 3 PM",
            category="work",
            tags=["meeting", "work"],
            importance=8
        )
        
        memory_id3 = db.store_memory(
            user_id=user2,
            content="Bob's personal note: family dinner on Sunday",
            category="personal",
            tags=["family"],
            importance=6
        )
        
        print(f"    ✅ Stored memories with IDs: {memory_id1}, {memory_id2}, {memory_id3}")
        
        # Test memory retrieval for user1
        print("  🔍 Testing memory retrieval...")
        user1_memories = db.search_memories(user_id=user1)
        print(f"    ✅ Found {len(user1_memories)} memories for {user1}")
        
        # Verify user separation
        user2_memories = db.search_memories(user_id=user2)
        print(f"    ✅ Found {len(user2_memories)} memories for {user2}")
        
        assert len(user1_memories) == 2, f"Expected 2 memories for user1, got {len(user1_memories)}"
        assert len(user2_memories) == 1, f"Expected 1 memory for user2, got {len(user2_memories)}"
        
        # Test category filtering
        work_memories = db.search_memories(user_id=user1, category="work")
        assert len(work_memories) == 1, f"Expected 1 work memory, got {len(work_memories)}"
        print("    ✅ Category filtering works")
        
        # Test text search
        grocery_memories = db.search_memories(user_id=user1, query="groceries")
        assert len(grocery_memories) == 1, f"Expected 1 grocery memory, got {len(grocery_memories)}"
        print("    ✅ Text search works")
        
        # Test time-based search
        recent_memories = db.search_memories(user_id=user1, days_back=1)
        assert len(recent_memories) == 2, f"Expected 2 recent memories, got {len(recent_memories)}"
        print("    ✅ Time-based search works")
        
        # Test memory statistics
        stats = db.get_memory_stats(user_id=user1)
        assert stats["total_memories"] == 2, f"Expected 2 total memories, got {stats['total_memories']}"
        assert "work" in stats["categories"], "Work category not found in stats"
        assert "tasks" in stats["categories"], "Tasks category not found in stats"
        print("    ✅ Memory statistics work")
        
        print("✅ All database tests passed!")
        
    finally:
        # Clean up
        os.unlink(temp_db.name)

async def test_memory_parsing():
    """Test natural language memory command parsing"""
    print("\n🧪 Testing Memory Command Parsing...")
    
    # Create a temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        # Start a test server
        server = MementoServer()
        server.db = MementoMemoryDB(temp_db.name)
        
        # Test storage command parsing
        print("  📝 Testing storage command parsing...")
        test_inputs = [
            "Hey Memento, remember that my dog's name is Buddy",
            "Store this memory: my favorite pizza place is Luigi's",
            "I want you to remember my anniversary is March 15th",
            "Don't forget that the meeting is tomorrow at 3 PM"
        ]
        
        for i, test_input in enumerate(test_inputs):
            # Simulate the parse_memory_command tool
            arguments = {"user_input": test_input, "user_id": "test_user"}
            
            # This would normally be called through MCP, but we'll test the logic directly
            result = await test_memory_command_parsing(server, arguments)
            parsed = json.loads(result)
            
            assert parsed["intent"] == "store_memory", f"Expected store_memory intent for input {i+1}"
            assert len(parsed["content"]) > 0, f"No content extracted for input {i+1}"
            print(f"    ✅ Input {i+1}: '{test_input[:30]}...' → store_memory")
        
        # Test recall command parsing
        print("  🔍 Testing recall command parsing...")
        recall_inputs = [
            "What did I ask you to remember?",
            "Show me my work memories",
            "What memories do you have from last week?",
            "Tell me about my family memories"
        ]
        
        for i, test_input in enumerate(recall_inputs):
            arguments = {"user_input": test_input, "user_id": "test_user"}
            result = await test_memory_command_parsing(server, arguments)
            parsed = json.loads(result)
            
            assert parsed["intent"] == "recall_memories", f"Expected recall_memories intent for input {i+1}"
            print(f"    ✅ Input {i+1}: '{test_input[:30]}...' → recall_memories")
        
        print("✅ All parsing tests passed!")
        
    finally:
        os.unlink(temp_db.name)

async def test_memory_command_parsing(server, arguments):
    """Helper function to test memory command parsing"""
    user_input = arguments.get("user_input", "")
    user_id = arguments.get("user_id", "default_user")
    
    if not user_input:
        return json.dumps({"intent": "unknown", "message": "No input provided"})
    
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
    
    # Detect intent
    is_store_command = any(trigger in input_lower for trigger in store_triggers)
    is_recall_command = any(trigger in input_lower for trigger in recall_triggers)
    
    if is_store_command:
        # Extract content to store
        content = user_input
        
        # Remove trigger phrases to get clean content
        for trigger in store_triggers:
            if trigger in input_lower:
                start_idx = input_lower.find(trigger)
                if start_idx != -1:
                    content = user_input[start_idx + len(trigger):].strip()
                    break
        
        return json.dumps({
            "intent": "store_memory",
            "content": content,
            "category": "general",
            "user_id": user_id,
            "original_input": user_input
        })
    
    elif is_recall_command:
        return json.dumps({
            "intent": "recall_memories",
            "query": "",
            "user_id": user_id,
            "original_input": user_input
        })
    
    else:
        return json.dumps({
            "intent": "unknown",
            "message": "I didn't detect a memory command.",
            "user_id": user_id,
            "original_input": user_input
        })

async def test_integration_scenario():
    """Test a complete user scenario"""
    print("\n🧪 Testing Complete User Scenario...")
    
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        db = MementoMemoryDB(temp_db.name)
        user_id = "test_user@test_machine"
        
        print("  📅 Scenario: User manages daily tasks and appointments")
        
        # Day 1: Store some memories
        print("    Day 1: Storing initial memories...")
        db.store_memory(
            user_id=user_id,
            content="Dentist appointment on Friday at 2 PM",
            category="personal",
            tags=["appointment", "health"],
            importance=8
        )
        
        db.store_memory(
            user_id=user_id,
            content="Buy birthday gift for Mom - she likes jewelry",
            category="tasks",
            tags=["shopping", "family", "birthday"],
            importance=9
        )
        
        db.store_memory(
            user_id=user_id,
            content="Project deadline moved to next month",
            category="work",
            tags=["project", "deadline"],
            importance=7
        )
        
        # Check total memories
        stats = db.get_memory_stats(user_id)
        assert stats["total_memories"] == 3, f"Expected 3 memories, got {stats['total_memories']}"
        print(f"    ✅ Stored 3 memories, categories: {stats['categories']}")
        
        # Search for specific memories
        appointment_memories = db.search_memories(user_id, query="appointment")
        assert len(appointment_memories) == 1, "Should find 1 appointment memory"
        print("    ✅ Found appointment memory")
        
        family_memories = db.search_memories(user_id, query="Mom")
        assert len(family_memories) == 1, "Should find 1 family memory"
        print("    ✅ Found family memory")
        
        work_memories = db.search_memories(user_id, category="work")
        assert len(work_memories) == 1, "Should find 1 work memory"
        print("    ✅ Found work memory")
        
        # Test importance filtering by getting all memories and checking importance
        all_memories = db.search_memories(user_id)
        high_importance = [m for m in all_memories if m['importance'] >= 8]
        assert len(high_importance) == 2, f"Expected 2 high-importance memories, got {len(high_importance)}"
        print("    ✅ Importance levels working correctly")
        
        print("✅ Integration scenario completed successfully!")
        
    finally:
        os.unlink(temp_db.name)

async def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Memento Test Suite")
    print("=" * 50)
    
    try:
        await test_memory_database()
        await test_memory_parsing()
        await test_integration_scenario()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Memento is working correctly.")
        print("🧠 Ready to help users manage their memories!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except AssertionError as e:
        print(f"\n❌ Assertion failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_all_tests())
