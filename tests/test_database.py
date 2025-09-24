#!/usr/bin/env python3
"""
Database operations tests for Flickr Local Browser
Tests the core database functionality including the key many-to-many photo-album relationships
"""

import pytest
import sqlite3
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from server import EnhancedFlickrServer


def create_empty_database(temp_dir):
    """Helper function to create empty database with schema only"""
    db_path = temp_dir / "flickr_metadata.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create albums table
    cursor.execute("""
        CREATE TABLE albums (
            id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            photo_count INTEGER,
            created_date TEXT,
            updated_date TEXT
        )
    """)
    
    # Create photos table
    cursor.execute("""
        CREATE TABLE photos (
            id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            tags TEXT,
            date_taken TEXT,
            date_uploaded TEXT,
            views INTEGER,
            url TEXT,
            thumbnail_url TEXT,
            width INTEGER,
            height INTEGER,
            size INTEGER,
            media_type TEXT,
            license TEXT,
            privacy TEXT,
            safety_level INTEGER,
            rotation INTEGER
        )
    """)
    
    # Create photo_albums junction table (many-to-many relationship)
    cursor.execute("""
        CREATE TABLE photo_albums (
            photo_id TEXT,
            album_id TEXT,
            PRIMARY KEY (photo_id, album_id),
            FOREIGN KEY (photo_id) REFERENCES photos (id),
            FOREIGN KEY (album_id) REFERENCES albums (id)
        )
    """)
    
    # Create comments table
    cursor.execute("""
        CREATE TABLE comments (
            id TEXT PRIMARY KEY,
            photo_id TEXT,
            author TEXT,
            content TEXT,
            comment_date TEXT,
            FOREIGN KEY (photo_id) REFERENCES photos (id)
        )
    """)
    
    conn.commit()
    conn.close()
    return db_path


def create_populated_database(temp_dir):
    """Helper function to create database with test data"""
    db_path = create_empty_database(temp_dir)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Sample albums
    sample_albums = [
        ('album1', 'Test Album 1', 'First test album', 2, '2023-01-01', '2023-01-02'),
        ('album2', 'Test Album 2', 'Second test album', 1, '2023-02-01', '2023-02-02')
    ]
    
    # Insert albums
    for album in sample_albums:
        cursor.execute("""
            INSERT INTO albums (id, title, description, photo_count, created_date, updated_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, album)
    
    # Sample photos
    sample_photos = [
        ('photo1', 'Sunset Photo', 'Beautiful sunset over the mountains', 'sunset, nature, landscape', '2023-01-15', '2023-01-16', 150),
        ('photo2', 'City Night', 'Downtown skyline at night', 'city, night, urban, architecture', '2023-01-20', '2023-01-21', 89),
        ('photo3', 'Beach Vacation', 'Relaxing day at the beach', 'beach, vacation, summer, ocean', '2023-02-10', '2023-02-11', 203)
    ]
    
    # Insert photos
    for photo_data in sample_photos:
        photo_id, title, desc, tags, date_taken, date_uploaded, views = photo_data
        cursor.execute("""
            INSERT INTO photos (id, title, description, tags, date_taken, date_uploaded,
                              views, url, thumbnail_url, width, height, size, media_type,
                              license, privacy, safety_level, rotation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (photo_id, title, desc, tags, date_taken, date_uploaded, views,
              f'https://example.com/{photo_id}.jpg', f'https://example.com/thumb_{photo_id}.jpg',
              1920, 1080, 2048000, 'photo', '0', 'public', 1, 0))
    
    # Create photo-album associations (many-to-many relationships)
    # Photo1 and Photo2 in Album1, Photo3 in Album2
    cursor.execute("INSERT INTO photo_albums (photo_id, album_id) VALUES (?, ?)", ('photo1', 'album1'))
    cursor.execute("INSERT INTO photo_albums (photo_id, album_id) VALUES (?, ?)", ('photo2', 'album1'))
    cursor.execute("INSERT INTO photo_albums (photo_id, album_id) VALUES (?, ?)", ('photo3', 'album2'))
    
    # Add some comments
    cursor.execute("""
        INSERT INTO comments (id, photo_id, author, content, comment_date)
        VALUES (?, ?, ?, ?, ?)
    """, ('comment1', 'photo1', 'John Doe', 'Amazing sunset!', '2023-01-17'))
    
    cursor.execute("""
        INSERT INTO comments (id, photo_id, author, content, comment_date)  
        VALUES (?, ?, ?, ?, ?)
    """, ('comment2', 'photo1', 'Jane Smith', 'Love the colors', '2023-01-18'))
    
    conn.commit()
    conn.close()
    return db_path


class TestDatabaseSchema:
    """Test database schema and structure"""
    
    def test_database_tables_exist(self):
        """Test that all required tables exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = create_empty_database(temp_path)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['albums', 'photos', 'photo_albums', 'comments']
            for table in expected_tables:
                assert table in tables, f"Table {table} should exist"
            
            conn.close()
    
    def test_albums_table_schema(self):
        """Test albums table has correct columns"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = create_empty_database(temp_path)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(albums)")
            columns = [row[1] for row in cursor.fetchall()]  # column names are at index 1
            
            expected_columns = ['id', 'title', 'description', 'photo_count', 'created_date', 'updated_date']
            for col in expected_columns:
                assert col in columns, f"Albums table should have column {col}"
            
            conn.close()
    
    def test_photos_table_schema(self):
        """Test photos table has correct columns"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = create_empty_database(temp_path)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(photos)")
            columns = [row[1] for row in cursor.fetchall()]
            
            expected_columns = ['id', 'title', 'description', 'tags', 'date_taken', 'views']
            for col in expected_columns:
                assert col in columns, f"Photos table should have column {col}"
            
            conn.close()
    
    def test_photo_albums_junction_table(self):
        """Test the critical many-to-many junction table exists and has correct structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = create_empty_database(temp_path)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(photo_albums)")
            columns = [row[1] for row in cursor.fetchall()]
            
            assert 'photo_id' in columns, "Junction table should have photo_id"
            assert 'album_id' in columns, "Junction table should have album_id"
            
            # Test foreign key constraints exist
            cursor.execute("PRAGMA foreign_key_list(photo_albums)")
            foreign_keys = cursor.fetchall()
            assert len(foreign_keys) >= 2, "Junction table should have foreign key constraints"
            
            conn.close()


class TestAlbumOperations:
    """Test album CRUD operations"""
    
    def test_get_albums_empty(self):
        """Test getting albums from empty database"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = create_empty_database(temp_path)
            
            # Create thumbnails directory
            thumbnails_dir = temp_path / "thumbnails"
            thumbnails_dir.mkdir(exist_ok=True)
            
            # Test with empty database
            server = EnhancedFlickrServer(data_dir=str(temp_path))
            albums = server.get_albums()
            assert isinstance(albums, list)
            assert len(albums) == 0
    
    def test_get_albums_with_data(self):
        """Test getting albums with populated data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = create_populated_database(temp_path)
            
            # Create thumbnails directory
            thumbnails_dir = temp_path / "thumbnails"
            thumbnails_dir.mkdir(exist_ok=True)
            
            server = EnhancedFlickrServer(data_dir=str(temp_path))
            albums = server.get_albums()
            
            assert len(albums) == 2
            assert albums[0]['title'] in ['Test Album 1', 'Test Album 2']
            assert albums[1]['title'] in ['Test Album 1', 'Test Album 2']
            
            # Check that each album has all required fields
            for album in albums:
                assert 'id' in album
                assert 'title' in album
                assert 'description' in album
                assert 'photo_count' in album
    
    def test_album_photo_counts_from_junction_table(self):
        """Test that album photo counts come from junction table, not stored counts"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = create_populated_database(temp_path)
            
            # Create thumbnails directory
            thumbnails_dir = temp_path / "thumbnails"
            thumbnails_dir.mkdir(exist_ok=True)
            
            server = EnhancedFlickrServer(data_dir=str(temp_path))
            albums = server.get_albums()
            
            # Find specific albums and check their counts
            album1 = next(a for a in albums if a['id'] == 'album1')
            album2 = next(a for a in albums if a['id'] == 'album2')
            
            # Album1 should have 2 photos (photo1, photo2)
            # Album2 should have 1 photo (photo3)
            assert album1['photo_count'] == 2, "Album1 should have 2 photos from junction table"
            assert album2['photo_count'] == 1, "Album2 should have 1 photo from junction table"


# Only include the most critical tests for now to avoid fixture conflicts
class TestPhotoAlbumRelationships:
    """Test the critical many-to-many photo-album relationships"""
    
    def test_photo_can_belong_to_multiple_albums(self):
        """Test that a photo can be associated with multiple albums"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = create_populated_database(temp_path)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Add photo1 to album2 as well (so it's in both album1 and album2)
            cursor.execute("INSERT INTO photo_albums (photo_id, album_id) VALUES (?, ?)", 
                          ('photo1', 'album2'))
            conn.commit()
            
            # Verify photo1 is now in both albums
            cursor.execute("SELECT album_id FROM photo_albums WHERE photo_id = ?", ('photo1',))
            albums_for_photo1 = [row[0] for row in cursor.fetchall()]
            
            assert 'album1' in albums_for_photo1
            assert 'album2' in albums_for_photo1
            assert len(albums_for_photo1) == 2
            
            conn.close()


class TestSearchFunctionality:
    """Test advanced search capabilities"""
    
    def test_case_insensitive_search(self):
        """Test that search is case insensitive"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = create_populated_database(temp_path)
            
            # Create thumbnails directory
            thumbnails_dir = temp_path / "thumbnails"
            thumbnails_dir.mkdir(exist_ok=True)
            
            server = EnhancedFlickrServer(data_dir=str(temp_path))
            
            # Search with different cases
            results1 = server.get_photos(search_term='SUNSET')
            results2 = server.get_photos(search_term='sunset')
            results3 = server.get_photos(search_term='Sunset')
            
            assert len(results1) == 1
            assert len(results2) == 1
            assert len(results3) == 1
            assert results1[0]['id'] == results2[0]['id'] == results3[0]['id']
    
    def test_multi_field_search(self):
        """Test search across title, description, and tags"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = create_populated_database(temp_path)
            
            # Create thumbnails directory
            thumbnails_dir = temp_path / "thumbnails"
            thumbnails_dir.mkdir(exist_ok=True)
            
            server = EnhancedFlickrServer(data_dir=str(temp_path))
            
            # Word appears in title
            title_results = server.get_photos(search_term='Sunset')
            assert len(title_results) == 1
            
            # Word appears in description
            desc_results = server.get_photos(search_term='Downtown')  
            assert len(desc_results) == 1
            
            # Word appears in tags
            tag_results = server.get_photos(search_term='urban')
            assert len(tag_results) == 1
