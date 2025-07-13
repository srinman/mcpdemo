#!/usr/bin/env python3
"""
Simple validation script for file-based Memento system
"""

import tempfile
import shutil
import json
from pathlib import Path

print("🧪 Testing Memento File-Based System...")

# Test imports
try:
    from memento_server_files import MementoFileManager, MementoParser
    print("✅ Imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit(1)

# Create temp directory
temp_dir = Path(tempfile.mkdtemp(prefix="memento_test_"))
print(f"📁 Test directory: {temp_dir}")

try:
    # Test file manager
    fm = MementoFileManager(temp_dir)
    print("✅ File manager created")
    
    # Test storing memory
    memory_id = fm.store_memory("test_user", "Test memory content", "test")
    print(f"✅ Memory stored with ID: {memory_id}")
    
    # Test loading memories
    memories = fm.search_memories("test_user")
    print(f"✅ Found {len(memories)} memories")
    
    # Test summary
    summary = fm.get_memory_summary("test_user")
    print(f"✅ Summary: {summary['total_memories']} total memories")
    
    # Test file exists
    files = list(temp_dir.glob("*.json"))
    print(f"✅ Created {len(files)} files")
    
    # Test file content
    if files:
        with open(files[0], 'r') as f:
            data = json.load(f)
        print(f"✅ File contains {len(data.get('memories', []))} memories")
    
    print("🎉 All basic tests passed!")
    
finally:
    # Cleanup
    shutil.rmtree(temp_dir)
    print(f"🗑️ Cleaned up {temp_dir}")
