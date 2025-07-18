#!/usr/bin/env python3
"""
Demo script for Memento MCP Server with OAuth
This demonstrates the functionality without requiring full Azure AD setup
"""

import json
import os
from pathlib import Path
import datetime
import uuid
import hashlib

class MementoDemo:
    def __init__(self):
        self.user_data_dir = Path("user_data")
        self.user_data_dir.mkdir(exist_ok=True)
        
        # Demo users
        self.demo_users = {
            "alice": {
                "user_id": "alice123",
                "user_name": "Alice Smith",
                "user_email": "alice@example.com"
            },
            "bob": {
                "user_id": "bob456", 
                "user_name": "Bob Johnson",
                "user_email": "bob@example.com"
            }
        }
        
        self.current_user = None
        self.current_user_dir = None
    
    def switch_user(self, username):
        """Switch to a different demo user"""
        if username in self.demo_users:
            self.current_user = self.demo_users[username]
            user_hash = hashlib.md5(self.current_user["user_id"].encode()).hexdigest()[:8]
            self.current_user_dir = self.user_data_dir / f"user_{user_hash}"
            self.current_user_dir.mkdir(exist_ok=True)
            
            # Create files subdirectory
            (self.current_user_dir / "files").mkdir(exist_ok=True)
            
            print(f"✅ Switched to user: {self.current_user['user_name']}")
            return True
        else:
            print(f"❌ User '{username}' not found")
            return False
    
    def store_memento(self, content, title=None, tags=None):
        """Store a memento for the current user"""
        if not self.current_user:
            print("❌ No user selected. Use switch_user() first.")
            return False
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if not title:
            title = f"memento_{timestamp}"
        
        filename = f"{title}_{timestamp}.json"
        filepath = self.current_user_dir / filename
        
        memento_data = {
            "id": str(uuid.uuid4()),
            "title": title,
            "content": content,
            "tags": tags or [],
            "created_at": datetime.datetime.now().isoformat(),
            "user_id": self.current_user["user_id"],
            "user_name": self.current_user["user_name"]
        }
        
        with open(filepath, 'w') as f:
            json.dump(memento_data, f, indent=2)
        
        print(f"✅ Memento '{title}' stored for {self.current_user['user_name']}")
        return True
    
    def retrieve_mementos(self, query=None, days_back=7):
        """Retrieve mementos for the current user"""
        if not self.current_user:
            print("❌ No user selected. Use switch_user() first.")
            return []
        
        memento_files = list(self.current_user_dir.glob("*.json"))
        if not memento_files:
            print(f"📭 No mementos found for {self.current_user['user_name']}")
            return []
        
        mementos = []
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
        
        for file in memento_files:
            try:
                with open(file, 'r') as f:
                    memento = json.load(f)
                
                # Check date filter
                created_at = datetime.datetime.fromisoformat(memento["created_at"])
                if created_at < cutoff_date:
                    continue
                
                # Check query filter
                if query:
                    query_lower = query.lower()
                    if (query_lower not in memento["content"].lower() and
                        query_lower not in memento["title"].lower() and
                        not any(query_lower in tag.lower() for tag in memento["tags"])):
                        continue
                
                mementos.append(memento)
            except Exception:
                continue
        
        # Sort by creation date (newest first)
        mementos.sort(key=lambda x: x["created_at"], reverse=True)
        
        print(f"📋 Found {len(mementos)} memento(s) for {self.current_user['user_name']}:")
        for memento in mementos:
            print(f"  📝 {memento['title']}")
            print(f"     Created: {memento['created_at']}")
            print(f"     Content: {memento['content'][:100]}{'...' if len(memento['content']) > 100 else ''}")
            if memento['tags']:
                print(f"     Tags: {', '.join(memento['tags'])}")
            print()
        
        return mementos
    
    def store_file_memento(self, filename, content, description=None):
        """Store a file as a memento"""
        if not self.current_user:
            print("❌ No user selected. Use switch_user() first.")
            return False
        
        files_dir = self.current_user_dir / "files"
        file_path = files_dir / filename
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        memento_data = {
            "id": str(uuid.uuid4()),
            "title": f"File: {filename}",
            "description": description or f"Stored file: {filename}",
            "filename": filename,
            "file_path": str(file_path),
            "file_size": len(content),
            "created_at": datetime.datetime.now().isoformat(),
            "user_id": self.current_user["user_id"],
            "user_name": self.current_user["user_name"],
            "type": "file"
        }
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        memento_file = self.current_user_dir / f"file_{filename}_{timestamp}.json"
        with open(memento_file, 'w') as f:
            json.dump(memento_data, f, indent=2)
        
        print(f"✅ File '{filename}' stored as memento for {self.current_user['user_name']}")
        return True
    
    def retrieve_file_memento(self, filename):
        """Retrieve a file memento"""
        if not self.current_user:
            print("❌ No user selected. Use switch_user() first.")
            return None
        
        memento_files = list(self.current_user_dir.glob(f"file_{filename}_*.json"))
        if not memento_files:
            print(f"📭 File '{filename}' not found in mementos for {self.current_user['user_name']}")
            return None
        
        # Get the most recent file
        memento_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        memento_file = memento_files[0]
        
        with open(memento_file, 'r') as f:
            memento = json.load(f)
        
        file_path = Path(memento["file_path"])
        if file_path.exists():
            with open(file_path, 'r') as f:
                file_content = f.read()
            
            print(f"📄 File: {filename}")
            print(f"   Description: {memento['description']}")
            print(f"   Created: {memento['created_at']}")
            print(f"   Size: {memento['file_size']} characters")
            print(f"   Content:\n{file_content}")
            
            return file_content
        else:
            print(f"❌ File '{filename}' record found but file is missing")
            return None
    
    def list_users(self):
        """List all users with stored data"""
        user_dirs = [d for d in self.user_data_dir.iterdir() if d.is_dir() and d.name.startswith("user_")]
        
        print(f"👥 Users with stored data ({len(user_dirs)} total):")
        for user_dir in user_dirs:
            memento_files = list(user_dir.glob("*.json"))
            file_count = len(memento_files)
            
            # Try to get user info
            user_info = "Unknown"
            if memento_files:
                try:
                    with open(memento_files[0], 'r') as f:
                        sample_memento = json.load(f)
                        user_info = sample_memento.get("user_name", "Unknown")
                except:
                    pass
            
            print(f"  📁 {user_dir.name}: {user_info} ({file_count} mementos)")
    
    def demo_natural_language_scenarios(self):
        """Demonstrate natural language scenarios"""
        print("\n🎯 Natural Language Scenarios Demo")
        print("=" * 50)
        
        scenarios = [
            {
                "user_input": "Hey memento, store this file called 'meeting_notes.txt'",
                "interpretation": "User wants to store a file",
                "action": lambda: self.store_file_memento(
                    "meeting_notes.txt", 
                    "Meeting with team about Q1 planning\n- Discussed budget allocation\n- Set milestone dates\n- Assigned responsibilities",
                    "Meeting notes from Q1 planning session"
                )
            },
            {
                "user_input": "Remember that I need to call John tomorrow",
                "interpretation": "User wants to store a reminder",
                "action": lambda: self.store_memento(
                    "Need to call John tomorrow about the project update",
                    "Call John Reminder",
                    ["reminder", "urgent"]
                )
            },
            {
                "user_input": "Store this code snippet for later",
                "interpretation": "User wants to store code",
                "action": lambda: self.store_memento(
                    "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
                    "Fibonacci Function",
                    ["code", "python", "algorithm"]
                )
            },
            {
                "user_input": "What did I store yesterday?",
                "interpretation": "User wants to retrieve recent mementos",
                "action": lambda: self.retrieve_mementos(days_back=1)
            },
            {
                "user_input": "Find my notes about meetings",
                "interpretation": "User wants to search for meeting-related content",
                "action": lambda: self.retrieve_mementos(query="meeting")
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n--- Scenario {i} ---")
            print(f"User says: '{scenario['user_input']}'")
            print(f"Interpretation: {scenario['interpretation']}")
            print("Action:")
            scenario["action"]()

def main():
    print("🧠 Memento MCP Server Demo")
    print("=" * 50)
    print("This demo shows how the Memento system works without requiring OAuth setup")
    print()
    
    demo = MementoDemo()
    
    # Demo for Alice
    print("👤 Demo for Alice:")
    demo.switch_user("alice")
    demo.store_memento("I love working with Python and AI", "Python Interest", ["programming", "ai"])
    demo.store_memento("Meeting with Bob about the project went well", "Project Meeting", ["work", "meeting"])
    demo.store_file_memento("todo.txt", "1. Review code\n2. Write documentation\n3. Test features", "My todo list")
    
    print("\n📋 Alice's mementos:")
    demo.retrieve_mementos()
    
    # Demo for Bob
    print("\n👤 Demo for Bob:")
    demo.switch_user("bob")
    demo.store_memento("Need to prepare for the presentation next week", "Presentation Prep", ["work", "presentation"])
    demo.store_memento("Alice's project ideas are really innovative", "Alice's Ideas", ["collaboration", "ideas"])
    demo.store_file_memento("script.py", "print('Hello from Bob!')\n# This is Bob's script", "Bob's Python script")
    
    print("\n📋 Bob's mementos:")
    demo.retrieve_mementos()
    
    # Show user isolation
    print("\n🔒 User Isolation Demo:")
    demo.switch_user("alice")
    print("Alice searching for 'presentation':")
    demo.retrieve_mementos(query="presentation")
    
    demo.switch_user("bob")
    print("Bob searching for 'presentation':")
    demo.retrieve_mementos(query="presentation")
    
    # Show file retrieval
    print("\n📄 File Retrieval Demo:")
    demo.switch_user("alice")
    demo.retrieve_file_memento("todo.txt")
    
    demo.switch_user("bob")
    demo.retrieve_file_memento("script.py")
    
    # Show all users
    print("\n👥 All Users:")
    demo.list_users()
    
    # Natural language scenarios
    demo.switch_user("alice")
    demo.demo_natural_language_scenarios()
    
    print("\n🎉 Demo Complete!")
    print("This shows how the system would work with OAuth authentication.")
    print("Each user's data is completely isolated and secure.")

if __name__ == "__main__":
    main()
