import json
import tempfile
from pathlib import Path

# Direct test without imports
temp_dir = Path(tempfile.mkdtemp())
print(f"Created temp dir: {temp_dir}")

# Create a test file
test_file = temp_dir / "test.json"
test_data = {"user_id": "test", "memories": [{"id": 1, "content": "test"}]}

with open(test_file, 'w') as f:
    json.dump(test_data, f)

print(f"Created file: {test_file}")

# Read it back
with open(test_file, 'r') as f:
    loaded = json.load(f)

print(f"Loaded data: {loaded}")
print("Direct file test successful!")

# Cleanup
import shutil
shutil.rmtree(temp_dir)
print("Cleanup complete")
