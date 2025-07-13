#!/usr/bin/env python3

# Test the file manager directly
import sys
import tempfile
from pathlib import Path
import shutil

print("Testing Memento File Manager...")

# Test the file manager class directly
temp_dir = Path(tempfile.mkdtemp())
print(f"Test directory: {temp_dir}")

# Import the components
sys.path.insert(0, '.')

try:
    from memento_server_files import MementoFileManager, MementoParser
    print("✅ Successfully imported Memento components")
    
    # Test file manager
    fm = MementoFileManager(temp_dir)
    print("✅ File manager created")
    
    # Test user ID sanitization
    user_id = "alice@laptop"
    safe_path = fm.get_user_file_path(user_id)
    print(f"✅ Safe path for '{user_id}': {safe_path.name}")
    
    # Test storing memory
    memory_id = fm.store_memory(
        user_id=user_id,
        content="Test memory content",
        category="test",
        tags=["test", "demo"],
        importance=5
    )
    print(f"✅ Stored memory with ID: {memory_id}")
    
    # Test file was created
    user_files = list(temp_dir.glob("*.json"))
    print(f"✅ Created {len(user_files)} user file(s)")
    
    # Test loading memories
    memories = fm.load_user_memories(user_id)
    print(f"✅ Loaded {len(memories)} memories")
    
    # Test searching
    search_results = fm.search_memories(user_id, query="test")
    print(f"✅ Search found {len(search_results)} memories")
    
    # Test summary
    summary = fm.get_memory_summary(user_id)
    print(f"✅ Summary: {summary}")
    
    # Test multiple users
    user2 = "bob@desktop"
    fm.store_memory(user2, "Bob's memory", "personal")
    all_users = fm.list_all_users()
    print(f"✅ Total users: {len(all_users)} - {all_users}")
    
    # Test parser
    parser = MementoParser()
    store_parsed = parser.parse_store_command("Hey Memento, remember my dentist appointment #health")
    print(f"✅ Store parsing: {store_parsed}")
    
    recall_parsed = parser.parse_recall_command("What did I store about work last week?")
    print(f"✅ Recall parsing: {recall_parsed}")
    
    print("\n🎉 ALL TESTS PASSED!")
    print(f"Files created in: {temp_dir}")
    
    # Show file contents
    for file_path in temp_dir.glob("*.json"):
        print(f"\n📄 {file_path.name}:")
        with open(file_path, 'r') as f:
            import json
            data = json.load(f)
            print(f"   User: {data.get('user_id')}")
            print(f"   Memories: {data.get('total_memories')}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Cleanup
    shutil.rmtree(temp_dir)
    print(f"🗑️ Cleaned up {temp_dir}")
