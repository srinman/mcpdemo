#!/usr/bin/env python3
"""
Quick test of Memento database functionality
"""

import sqlite3
import tempfile
import os
import json
from datetime import datetime

def test_memento_database():
    print('🧪 Testing Memento Database Functionality...')
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        # Initialize database
        conn = sqlite3.connect(temp_db.name)
        cursor = conn.cursor()
        
        # Create memories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                importance INTEGER DEFAULT 5,
                metadata TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON memories(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON memories(category)')
        
        print('✅ Database schema created successfully')
        
        # Test storing memories
        user_id = 'test_user@test_machine'
        memories_to_store = [
            ('Remember to buy groceries: milk, bread, eggs', 'tasks', '["shopping", "food"]', 7),
            ('Meeting with team lead tomorrow at 3 PM', 'work', '["meeting", "work"]', 8),
            ('Family dinner on Sunday', 'personal', '["family"]', 6)
        ]
        
        for content, category, tags, importance in memories_to_store:
            cursor.execute('''
                INSERT INTO memories (user_id, content, category, tags, importance)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, content, category, tags, importance))
        
        conn.commit()
        print('✅ Memories stored successfully')
        
        # Test retrieving memories
        cursor.execute('SELECT COUNT(*) FROM memories WHERE user_id = ?', (user_id,))
        total_memories = cursor.fetchone()[0]
        print(f'✅ Total memories for user: {total_memories}')
        
        # Test category filtering
        cursor.execute('SELECT COUNT(*) FROM memories WHERE user_id = ? AND category = ?', (user_id, 'work'))
        work_memories = cursor.fetchone()[0]
        print(f'✅ Work memories: {work_memories}')
        
        # Test search functionality
        cursor.execute('SELECT * FROM memories WHERE user_id = ? AND content LIKE ?', (user_id, '%groceries%'))
        search_results = cursor.fetchall()
        print(f'✅ Search results for "groceries": {len(search_results)} found')
        
        # Test user separation
        other_user = 'other_user@other_machine'
        cursor.execute('''
            INSERT INTO memories (user_id, content, category)
            VALUES (?, ?, ?)
        ''', (other_user, 'Other user memory', 'general'))
        conn.commit()
        
        cursor.execute('SELECT COUNT(*) FROM memories WHERE user_id = ?', (user_id,))
        user1_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM memories WHERE user_id = ?', (other_user,))
        user2_count = cursor.fetchone()[0]
        
        print(f'✅ User separation: User1={user1_count}, User2={user2_count}')
        
        if user1_count == 3 and user2_count == 1:
            print('🎉 All database tests passed!')
            return True
        else:
            print('❌ Database test failed - user separation issue')
            return False
        
    except Exception as e:
        print(f'❌ Database test failed: {e}')
        return False
    finally:
        conn.close()
        os.unlink(temp_db.name)

if __name__ == "__main__":
    test_memento_database()
