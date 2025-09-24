#!/usr/bin/env python3
"""
Test script to directly launch the photo browser
"""

import sys
import os
from pathlib import Path

# Add src directory to path
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

def test_browser_launch():
    print("Testing photo browser launch...")
    
    # Check for database
    db_path = Path("data/flickr_metadata.db")
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return False
    
    # Check for thumbnails directory
    thumbnails_dir = Path("data/thumbnails")
    if not thumbnails_dir.exists():
        print(f"❌ Thumbnails directory not found at {thumbnails_dir}")
        return False
    
    print(f"✅ Database found: {db_path}")
    print(f"✅ Thumbnails directory found: {thumbnails_dir}")
    
    try:
        # Import the server
        from server import app as browser_app
        print("✅ Server module imported successfully")
        
        print("🚀 Starting browser on http://127.0.0.1:8081")
        print("Press Ctrl+C to stop")
        
        browser_app.run(host='127.0.0.1', port=8081, debug=True)
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    test_browser_launch()