#!/usr/bin/env python3
"""
PyTest configuration and fixtures for Flickr Local Browser tests
"""

import pytest
import sqlite3
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from server import EnhancedFlickrServer
from flask import Flask

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test data"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup after test
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def test_database(temp_dir):
    """Create a test database with proper schema"""
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

@pytest.fixture
def sample_albums():
    """Sample album data for testing"""
    return [
        {
            'id': 'album1',
            'title': 'Test Album 1',
            'description': 'First test album',
            'photo_count': 2,
            'created_date': '2023-01-01',
            'updated_date': '2023-01-02'
        },
        {
            'id': 'album2', 
            'title': 'Test Album 2',
            'description': 'Second test album',
            'photo_count': 1,
            'created_date': '2023-02-01',
            'updated_date': '2023-02-02'
        }
    ]

@pytest.fixture
def sample_photos():
    """Sample photo data for testing"""
    return [
        {
            'id': 'photo1',
            'title': 'Sunset Photo',
            'description': 'Beautiful sunset over the mountains',
            'tags': 'sunset, nature, landscape',
            'date_taken': '2023-01-15',
            'date_uploaded': '2023-01-16',
            'views': 150,
            'url': 'https://example.com/photo1.jpg',
            'thumbnail_url': 'https://example.com/thumb1.jpg',
            'width': 1920,
            'height': 1080,
            'size': 2048000,
            'media_type': 'photo',
            'license': '0',
            'privacy': 'public',
            'safety_level': 1,
            'rotation': 0
        },
        {
            'id': 'photo2',
            'title': 'City Night',
            'description': 'Downtown skyline at night',
            'tags': 'city, night, urban, architecture',
            'date_taken': '2023-01-20',
            'date_uploaded': '2023-01-21',
            'views': 89,
            'url': 'https://example.com/photo2.jpg',
            'thumbnail_url': 'https://example.com/thumb2.jpg',
            'width': 1600,
            'height': 900,
            'size': 1536000,
            'media_type': 'photo',
            'license': '0',
            'privacy': 'public',
            'safety_level': 1,
            'rotation': 0
        },
        {
            'id': 'photo3',
            'title': 'Beach Vacation',
            'description': 'Relaxing day at the beach',
            'tags': 'beach, vacation, summer, ocean',
            'date_taken': '2023-02-10',
            'date_uploaded': '2023-02-11', 
            'views': 203,
            'url': 'https://example.com/photo3.jpg',
            'thumbnail_url': 'https://example.com/thumb3.jpg',
            'width': 1920,
            'height': 1280,
            'size': 2304000,
            'media_type': 'photo',
            'license': '0',
            'privacy': 'public',
            'safety_level': 1,
            'rotation': 0
        }
    ]

@pytest.fixture
def populated_database(test_database, sample_albums, sample_photos, temp_dir):
    """Database populated with test data"""
    conn = sqlite3.connect(test_database)
    cursor = conn.cursor()
    
    # Insert albums
    for album in sample_albums:
        cursor.execute("""
            INSERT INTO albums (id, title, description, photo_count, created_date, updated_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (album['id'], album['title'], album['description'], album['photo_count'],
              album['created_date'], album['updated_date']))
    
    # Insert photos
    for photo in sample_photos:
        cursor.execute("""
            INSERT INTO photos (id, title, description, tags, date_taken, date_uploaded,
                              views, url, thumbnail_url, width, height, size, media_type,
                              license, privacy, safety_level, rotation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (photo['id'], photo['title'], photo['description'], photo['tags'],
              photo['date_taken'], photo['date_uploaded'], photo['views'], photo['url'],
              photo['thumbnail_url'], photo['width'], photo['height'], photo['size'],
              photo['media_type'], photo['license'], photo['privacy'], photo['safety_level'],
              photo['rotation']))
    
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
    
    # Create thumbnails directory
    thumbnails_dir = temp_dir / "thumbnails"
    thumbnails_dir.mkdir(exist_ok=True)
    
    return {
        'db_path': test_database,
        'data_dir': temp_dir,
        'thumbnails_dir': thumbnails_dir
    }

@pytest.fixture
def flickr_server(populated_database):
    """Create EnhancedFlickrServer instance with test data"""
    return EnhancedFlickrServer(data_dir=str(populated_database['data_dir']))

@pytest.fixture
def flask_app(flickr_server):
    """Create Flask test app using the actual server routes"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # Add the actual routes from server.py
    @app.route('/api/albums')
    def get_albums():
        from flask import jsonify
        try:
            albums = flickr_server.get_albums()
            return jsonify(albums)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/photos')
    def get_photos():
        from flask import request, jsonify
        try:
            album_id = request.args.get('album_id')
            search_term = request.args.get('search')
            
            # Use the same logic as the actual server
            if album_id:
                limit = None  
                offset = 0
            else:
                limit = int(request.args.get('limit', 1000))
                offset = int(request.args.get('offset', 0))
            
            photos = flickr_server.get_photos(album_id, search_term, limit, offset)
            return jsonify(photos)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/photos/<photo_id>')
    def get_photo_details(photo_id):
        from flask import jsonify
        try:
            photo = flickr_server.get_photo_details(photo_id)
            if photo:
                return jsonify(photo)
            else:
                return jsonify({'error': 'Photo not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app

@pytest.fixture 
def client(flask_app):
    """Create Flask test client"""
    return flask_app.test_client()
