#!/usr/bin/env python3
"""
Demo script for Memento File-Based Memory System
Demonstrates the key features and file-based storage capabilities.
"""

import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from memento_server_files import MementoFileManager, MementoParser


async def demo_memento_file_system():
    """Demonstrate the Memento File-Based Memory System."""
    print("🧠 Memento: AI Memory System (File-Based) Demo")
    print("=" * 60)
    
    # Create a demo directory
    demo_dir = Path(tempfile.mkdtemp(prefix="memento_demo_"))
    print(f"📁 Demo directory: {demo_dir}")
    
    try:
        # Initialize components
        file_manager = MementoFileManager(demo_dir)
        parser = MementoParser()
        
        print("\n✅ File-based memory system initialized")
        
        # Demo users
        alice = "alice@laptop"
        bob = "bob@desktop"
        
        print(f"\n👥 Demo Users:")
        print(f"  - {alice}")
        print(f"  - {bob}")
        
        print("\n" + "="*60)
        print("🎭 DEMO SCENARIO: Two users storing different memories")
        print("="*60)
        
        # Alice's memories
        print(f"\n👩 {alice} is storing memories...")
        print("-" * 30)
        
        alice_memories = [
            {
                "text": "Hey Memento, remember that my dentist appointment is next Tuesday at 2 PM #health #important",
                "display": "Dentist appointment reminder"
            },
            {
                "text": "Store this work task: Review Q4 budget by Friday #work #urgent",
                "display": "Work task about budget"
            },
            {
                "text": "Remember my favorite coffee shop is Blue Bottle on 5th Street #personal #coffee",
                "display": "Personal note about coffee shop"
            },
            {
                "text": "Important idea: Use file-based storage for better user data separation #ideas #tech",
                "display": "Technical idea"
            }
        ]
        
        for i, memory in enumerate(alice_memories, 1):
            print(f"  {i}. {memory['display']}")
            parsed = parser.parse_store_command(memory['text'])
            memory_id = file_manager.store_memory(
                user_id=alice,
                content=parsed['content'],
                category=parsed['category'],
                tags=parsed['tags'],
                importance=parsed['importance']
            )
            print(f"     ✅ Stored with ID {memory_id}")
        
        # Bob's memories
        print(f"\n👨 {bob} is storing memories...")
        print("-" * 30)
        
        bob_memories = [
            {
                "text": "Remember to call mom this weekend #family #personal",
                "display": "Family reminder"
            },
            {
                "text": "Store this meeting: Team standup every Monday at 9 AM #work #meetings",
                "display": "Work meeting schedule"
            },
            {
                "text": "Great book recommendation: The Pragmatic Programmer #books #learning",
                "display": "Book recommendation"
            }
        ]
        
        for i, memory in enumerate(bob_memories, 1):
            print(f"  {i}. {memory['display']}")
            parsed = parser.parse_store_command(memory['text'])
            memory_id = file_manager.store_memory(
                user_id=bob,
                content=parsed['content'],
                category=parsed['category'],
                tags=parsed['tags'],
                importance=parsed['importance']
            )
            print(f"     ✅ Stored with ID {memory_id}")
        
        print("\n" + "="*60)
        print("📂 FILE SYSTEM STATUS")
        print("="*60)
        
        # Show file system state
        files = list(demo_dir.glob("*.json"))
        print(f"\n📁 Files created: {len(files)}")
        for file_path in files:
            file_size = file_path.stat().st_size
            print(f"  📄 {file_path.name} ({file_size} bytes)")
        
        # Show file contents preview
        print(f"\n📖 File Contents Preview:")
        for file_path in files:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            print(f"\n  📄 {file_path.name}:")
            print(f"     User: {data.get('user_id', 'Unknown')}")
            print(f"     Total memories: {data.get('total_memories', 0)}")
            print(f"     Last updated: {data.get('last_updated', 'Unknown')}")
            
            # Show first memory as example
            if data.get('memories'):
                first_memory = data['memories'][0]
                print(f"     First memory: \"{first_memory.get('content', '')[:50]}...\"")
                print(f"     Category: {first_memory.get('category', 'None')}")
                print(f"     Tags: {first_memory.get('tags', [])}")
        
        print("\n" + "="*60)
        print("🔍 SEARCHING AND RETRIEVAL DEMO")
        print("="*60)
        
        # Alice's searches
        print(f"\n👩 {alice} searching her memories:")
        print("-" * 40)
        
        # Search all memories
        all_alice_memories = file_manager.search_memories(alice)
        print(f"📚 All memories: {len(all_alice_memories)} found")
        
        # Search by category
        work_memories = file_manager.search_memories(alice, category="work")
        print(f"💼 Work memories: {len(work_memories)} found")
        if work_memories:
            print(f"    Example: \"{work_memories[0]['content'][:60]}...\"")
        
        # Search by content
        dentist_memories = file_manager.search_memories(alice, query="dentist")
        print(f"🦷 Dentist memories: {len(dentist_memories)} found")
        if dentist_memories:
            print(f"    Found: \"{dentist_memories[0]['content']}\"")
        
        # Bob's searches
        print(f"\n👨 {bob} searching his memories:")
        print("-" * 40)
        
        # Search all memories
        all_bob_memories = file_manager.search_memories(bob)
        print(f"📚 All memories: {len(all_bob_memories)} found")
        
        # Search by category
        family_memories = file_manager.search_memories(bob, category="personal")
        print(f"👨‍👩‍👧‍👦 Personal memories: {len(family_memories)} found")
        if family_memories:
            print(f"    Example: \"{family_memories[0]['content'][:60]}...\"")
        
        # Cross-user search isolation test
        print(f"\n🔒 Data isolation test:")
        print("-" * 40)
        
        # Alice tries to search Bob's memories (should find nothing)
        alice_searching_bob_content = file_manager.search_memories(alice, query="mom")
        print(f"👩 Alice searching for 'mom': {len(alice_searching_bob_content)} found")
        print("    (Should be 0 - Alice can't see Bob's family memories)")
        
        # Bob tries to search Alice's memories (should find nothing)
        bob_searching_alice_content = file_manager.search_memories(bob, query="dentist")
        print(f"👨 Bob searching for 'dentist': {len(bob_searching_alice_content)} found")
        print("    (Should be 0 - Bob can't see Alice's appointment)")
        
        print("\n" + "="*60)
        print("📊 SUMMARY STATISTICS")
        print("="*60)
        
        # Get summaries
        alice_summary = file_manager.get_memory_summary(alice)
        bob_summary = file_manager.get_memory_summary(bob)
        
        print(f"\n👩 {alice} Summary:")
        print(f"   📝 Total memories: {alice_summary['total_memories']}")
        print(f"   📂 Categories: {alice_summary['categories']}")
        print(f"   🕒 Recent memories: {alice_summary['recent_memories']}")
        print(f"   📄 File: {alice_summary['file_path']}")
        
        print(f"\n👨 {bob} Summary:")
        print(f"   📝 Total memories: {bob_summary['total_memories']}")
        print(f"   📂 Categories: {bob_summary['categories']}")
        print(f"   🕒 Recent memories: {bob_summary['recent_memories']}")
        print(f"   📄 File: {bob_summary['file_path']}")
        
        print("\n" + "="*60)
        print("🗣️ NATURAL LANGUAGE PARSING DEMO")
        print("="*60)
        
        # Demo natural language understanding
        test_commands = [
            "Hey Memento, remember that I need to pick up dry cleaning tomorrow",
            "Store this important work meeting: All-hands meeting Friday at 10 AM",
            "What did I store about work last week?",
            "Show me personal memories from this month",
            "Find anything about meetings or appointments"
        ]
        
        print("\n🎯 Natural Language Command Processing:")
        for i, command in enumerate(test_commands, 1):
            print(f"\n{i}. User says: \"{command}\"")
            
            if any(word in command.lower() for word in ["remember", "store", "hey memento"]):
                parsed = parser.parse_store_command(command)
                print(f"   🧠 Understood as: STORE memory")
                print(f"   📝 Content: \"{parsed['content']}\"")
                print(f"   📂 Category: {parsed['category']}")
                print(f"   🏷️ Tags: {parsed['tags']}")
                print(f"   ⭐ Importance: {parsed['importance']}/10")
            else:
                parsed = parser.parse_recall_command(command)
                print(f"   🧠 Understood as: RECALL memories")
                print(f"   🔍 Search query: \"{parsed['query']}\"")
                print(f"   📂 Category filter: {parsed['category']}")
                print(f"   📅 Time filter: {parsed['days_back']} days back" if parsed['days_back'] else "   📅 Time filter: None")
        
        print("\n" + "="*60)
        print("🎉 DEMO COMPLETE")
        print("="*60)
        
        print(f"\n✨ Key Features Demonstrated:")
        print(f"   📁 File-based storage: Each user gets their own JSON file")
        print(f"   🔒 Data separation: Users cannot access each other's memories")
        print(f"   🗣️ Natural language: Commands parsed intelligently")
        print(f"   🔍 Smart search: Category, content, and time-based filtering")
        print(f"   📊 Statistics: Comprehensive memory summaries")
        print(f"   🛡️ Security: Safe filename generation and path validation")
        
        print(f"\n📈 Demo Results:")
        print(f"   👥 Users: 2")
        print(f"   📄 Files: {len(files)}")
        print(f"   💾 Total memories: {alice_summary['total_memories'] + bob_summary['total_memories']}")
        print(f"   📂 Storage location: {demo_dir}")
        
        # Show final file system state
        print(f"\n📁 Final File System State:")
        total_size = 0
        for file_path in demo_dir.glob("*.json"):
            size = file_path.stat().st_size
            total_size += size
            print(f"   📄 {file_path.name}: {size} bytes")
        print(f"   📊 Total storage: {total_size} bytes")
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Run the client: python memento_client_files.py")
        print(f"   2. Try natural language commands")
        print(f"   3. Explore Azure OpenAI integration")
        print(f"   4. Test user separation with different system users")
        
    finally:
        # Clean up
        cleanup = input(f"\n🗑️ Delete demo directory {demo_dir}? (y/N): ").lower().strip()
        if cleanup == 'y':
            shutil.rmtree(demo_dir)
            print(f"✅ Demo directory cleaned up")
        else:
            print(f"📁 Demo files preserved at: {demo_dir}")


if __name__ == "__main__":
    asyncio.run(demo_memento_file_system())
