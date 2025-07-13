#!/usr/bin/env python3
import sys
print("Starting test...", flush=True)

try:
    import tempfile
    import json
    from pathlib import Path
    print("Basic imports OK", flush=True)
    
    sys.path.insert(0, '.')
    from memento_server_files import MementoFileManager
    print("Memento import OK", flush=True)
    
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Temp dir: {temp_dir}", flush=True)
    
    fm = MementoFileManager(temp_dir)
    print("File manager created", flush=True)
    
    mid = fm.store_memory("test_user", "Test content", "test")
    print(f"Memory stored: {mid}", flush=True)
    
    memories = fm.search_memories("test_user")
    print(f"Found memories: {len(memories)}", flush=True)
    
    print("SUCCESS: All tests passed!", flush=True)
    
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()
