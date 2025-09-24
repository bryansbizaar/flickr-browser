#!/usr/bin/env python3
"""
Database inspector to check demo data structure and content
"""

import sqlite3
from pathlib import Path

def inspect_database():
    db_path = Path("data/flickr_metadata.db")
    
    if not db_path.exists():
        print("❌ Database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Database Schema Inspection")
    print("=" * 50)
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables: {tables}")
    
    for table in tables:
        print(f"\n📋 Table: {table}")
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        print("Columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Get sample data
        cursor.execute(f"SELECT * FROM {table} LIMIT 3;")
        rows = cursor.fetchall()
        
        if rows:
            print("\nSample data:")
            for i, row in enumerate(rows[:2]):
                print(f"  Row {i+1}: {dict(zip([col[1] for col in columns], row))}")
        
        # Get count
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"Total rows: {count}")
    
    print("\n🖼️ Photo Details Check")
    print("=" * 30)
    
    # Check a specific photo's details
    cursor.execute("""
        SELECT 
            id, title, description, tags, date_taken, date_uploaded, views,
            filename, thumbnail_path
        FROM photos 
        LIMIT 1
    """)
    
    photo = cursor.fetchone()
    if photo:
        print("Sample photo data:")
        columns = [desc[0] for desc in cursor.description]
        photo_dict = dict(zip(columns, photo))
        for key, value in photo_dict.items():
            print(f"  {key}: {value}")
    
    print("\n🔗 Photo-Album Associations Check")
    print("=" * 40)
    
    # Check associations
    cursor.execute("""
        SELECT 
            p.id as photo_id,
            p.title as photo_title,
            a.title as album_title
        FROM photos p
        JOIN photo_albums pa ON p.id = pa.photo_id
        JOIN albums a ON pa.album_id = a.id
        LIMIT 5
    """)
    
    associations = cursor.fetchall()
    print("Sample associations:")
    for assoc in associations:
        print(f"  '{assoc[1]}' is in '{assoc[2]}'")
    
    conn.close()

if __name__ == "__main__":
    inspect_database()
