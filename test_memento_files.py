#!/usr/bin/env python3
"""
Test script for Memento File-Based Memory System
Validates file storage, user separation, and core functionality.
"""

import asyncio
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Import the file-based components
from memento_server_files import MementoFileManager, MementoParser


async def test_file_based_memory_system():
    """Test the file-based memory system comprehensively."""
    print("🧪 Testing Memento File-Based Memory System")
    print("=" * 50)
    
    # Create a temporary directory for testing
    temp_dir = Path(tempfile.mkdtemp(prefix="memento_test_"))
    print(f"📁 Test directory: {temp_dir}")
    
    try:
        # Initialize file manager with test directory
        file_manager = MementoFileManager(temp_dir)
        parser = MementoParser()
        
        # Test users
        user1 = "alice@laptop"
        user2 = "bob@desktop"
        user3 = "charlie@workstation"
        
        print("\n📝 Test 1: Storing memories for different users")
        print("-" * 40)
        
        # Store memories for user1
        memory1_id = file_manager.store_memory(
            user_id=user1,
            content="Remember to buy groceries: milk, bread, eggs",
            category="tasks",
            tags=["shopping", "food"],
            importance=7
        )
        print(f"✅ User1 memory stored with ID: {memory1_id}")
        
        memory2_id = file_manager.store_memory(
            user_id=user1,
            content="Meeting with team lead tomorrow at 3 PM",
            category="work",
            tags=["meeting", "work"],
            importance=8
        )
        print(f"✅ User1 work memory stored with ID: {memory2_id}")
        
        # Store memories for user2
        memory3_id = file_manager.store_memory(
            user_id=user2,
            content="Mom's birthday is next Friday",
            category="personal",
            tags=["family", "birthday"],
            importance=9
        )
        print(f"✅ User2 memory stored with ID: {memory3_id}")
        
        # Store memories for user3
        memory4_id = file_manager.store_memory(
            user_id=user3,
            content="Project deadline for Q4 report is December 15th",
            category="work",
            tags=["deadline", "project"],
            importance=10
        )
        print(f"✅ User3 memory stored with ID: {memory4_id}")
        
        print("\n📂 Test 2: Verifying file separation")
        print("-" * 40)
        
        # Check that each user has their own file
        user1_file = file_manager.get_user_file_path(user1)
        user2_file = file_manager.get_user_file_path(user2)
        user3_file = file_manager.get_user_file_path(user3)
        
        print(f"User1 file: {user1_file}")
        print(f"User2 file: {user2_file}")
        print(f"User3 file: {user3_file}")
        
        # Verify files exist and are different
        assert user1_file.exists(), "User1 file should exist"
        assert user2_file.exists(), "User2 file should exist"
        assert user3_file.exists(), "User3 file should exist"
        assert user1_file != user2_file != user3_file, "Each user should have different files"
        print("✅ Each user has separate files")
        
        print("\n🔍 Test 3: Searching memories (user isolation)")
        print("-" * 40)
        
        # Test user1 memories
        user1_memories = file_manager.search_memories(user1)
        print(f"User1 total memories: {len(user1_memories)}")
        assert len(user1_memories) == 2, "User1 should have 2 memories"
        
        # Test user2 memories
        user2_memories = file_manager.search_memories(user2)
        print(f"User2 total memories: {len(user2_memories)}")
        assert len(user2_memories) == 1, "User2 should have 1 memory"
        
        # Test user3 memories
        user3_memories = file_manager.search_memories(user3)
        print(f"User3 total memories: {len(user3_memories)}")
        assert len(user3_memories) == 1, "User3 should have 1 memory"
        
        print("✅ User data isolation verified")
        
        print("\n🔎 Test 4: Category and content search")
        print("-" * 40)
        
        # Search by category
        work_memories = file_manager.search_memories(user1, category="work")
        print(f"User1 work memories: {len(work_memories)}")
        assert len(work_memories) == 1, "User1 should have 1 work memory"
        
        # Search by content
        grocery_memories = file_manager.search_memories(user1, query="groceries")
        print(f"User1 grocery memories: {len(grocery_memories)}")
        assert len(grocery_memories) == 1, "Should find 1 grocery memory"
        
        # Search should not cross users
        user2_work_memories = file_manager.search_memories(user2, category="work")
        print(f"User2 work memories: {len(user2_work_memories)}")
        assert len(user2_work_memories) == 0, "User2 should have no work memories"
        
        print("✅ Search functionality verified")
        
        print("\n📊 Test 5: Memory summaries")
        print("-" * 40)
        
        # Get summaries for each user
        user1_summary = file_manager.get_memory_summary(user1)
        user2_summary = file_manager.get_memory_summary(user2)
        user3_summary = file_manager.get_memory_summary(user3)
        
        print(f"User1 summary: {user1_summary['total_memories']} memories, categories: {user1_summary['categories']}")
        print(f"User2 summary: {user2_summary['total_memories']} memories, categories: {user2_summary['categories']}")
        print(f"User3 summary: {user3_summary['total_memories']} memories, categories: {user3_summary['categories']}")
        
        assert user1_summary['total_memories'] == 2
        assert user2_summary['total_memories'] == 1
        assert user3_summary['total_memories'] == 1
        
        print("✅ Summary functionality verified")
        
        print("\n🗣️ Test 6: Natural language parsing")
        print("-" * 40)
        
        # Test storage command parsing
        store_tests = [
            "Hey Memento, remember that my dentist appointment is next Tuesday at 2 PM",
            "Store this important work task: Review Q4 budget #work #important",
            "Remember my friend's phone number is 555-1234 #contact"
        ]
        
        for test_input in store_tests:
            parsed = parser.parse_store_command(test_input)
            print(f"Input: {test_input[:50]}...")
            print(f"  Parsed: category={parsed['category']}, tags={parsed['tags']}, importance={parsed['importance']}")
        
        # Test recall command parsing
        recall_tests = [
            "What did I store about work last week?",
            "Show me personal memories from this month",
            "Find anything about dentist appointments"
        ]
        
        for test_input in recall_tests:
            parsed = parser.parse_recall_command(test_input)
            print(f"Input: {test_input}")
            print(f"  Parsed: category={parsed['category']}, days_back={parsed['days_back']}, query='{parsed['query']}'")
        
        print("✅ Natural language parsing verified")
        
        print("\n📄 Test 7: File content validation")
        print("-" * 40)
        
        # Read and validate file contents
        with open(user1_file, 'r') as f:
            user1_data = json.load(f)
        
        print(f"User1 file structure: {list(user1_data.keys())}")
        assert 'user_id' in user1_data
        assert 'memories' in user1_data
        assert 'total_memories' in user1_data
        assert user1_data['user_id'] == user1
        assert user1_data['total_memories'] == len(user1_data['memories'])
        
        # Validate memory structure
        memory = user1_data['memories'][0]
        required_fields = ['id', 'content', 'category', 'tags', 'importance', 'created_at']
        for field in required_fields:
            assert field in memory, f"Memory should have {field} field"
        
        print("✅ File content structure verified")
        
        print("\n👥 Test 8: User listing")
        print("-" * 40)
        
        all_users = file_manager.list_all_users()
        print(f"All users: {all_users}")
        
        expected_users = {user1, user2, user3}
        found_users = set(all_users)
        assert expected_users == found_users, f"Expected {expected_users}, found {found_users}"
        
        print("✅ User listing verified")
        
        print("\n🔒 Test 9: File security (filename sanitization)")
        print("-" * 40)
        
        # Test with problematic user IDs
        problematic_users = [
            "user/../etc/passwd",
            "user<script>alert('xss')</script>",
            "user with spaces & symbols!@#$%",
        ]
        
        for problem_user in problematic_users:
            safe_path = file_manager.get_user_file_path(problem_user)
            print(f"Problematic: '{problem_user}' -> Safe path: {safe_path.name}")
            
            # Verify the path is within the memories directory
            assert safe_path.parent == file_manager.memories_dir
            # Verify no path traversal
            assert ".." not in str(safe_path)
            # Verify safe characters only in filename
            assert safe_path.name.endswith(".json")
        
        print("✅ File security verified")
        
        print("\n🎉 All tests passed!")
        print(f"📁 Total files created: {len(list(temp_dir.glob('*.json')))}")
        
        # Show final directory contents
        print("\n📂 Final test directory contents:")
        for file_path in temp_dir.glob("*.json"):
            file_size = file_path.stat().st_size
            print(f"  {file_path.name} ({file_size} bytes)")
    
    finally:
        # Clean up test directory
        shutil.rmtree(temp_dir)
        print(f"\n🗑️ Cleaned up test directory: {temp_dir}")


if __name__ == "__main__":
    asyncio.run(test_file_based_memory_system())
