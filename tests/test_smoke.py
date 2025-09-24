#!/usr/bin/env python3
"""
Simple smoke test to verify test setup works
"""

import pytest
import sqlite3
import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_basic_setup():
    """Basic test to verify pytest is working"""
    assert True

def test_can_import_server():
    """Test that we can import the server module"""
    try:
        from server import EnhancedFlickrServer
        assert EnhancedFlickrServer is not None
        print("✅ Successfully imported EnhancedFlickrServer")
    except ImportError as e:
        pytest.fail(f"Failed to import server module: {e}")

def test_can_create_database():
    """Test that we can create a test database"""
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("INSERT INTO test (name) VALUES ('hello')")
        conn.commit()
        
        cursor.execute("SELECT name FROM test")
        result = cursor.fetchone()
        assert result[0] == 'hello'
        
        conn.close()
        print("✅ Database operations working")

if __name__ == "__main__":
    # Run tests directly
    test_basic_setup()
    test_can_import_server()
    test_can_create_database()
    print("🎉 All smoke tests passed!")
