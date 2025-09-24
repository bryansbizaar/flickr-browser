#!/usr/bin/env python3
"""
API endpoints tests for Flickr Local Browser
Tests the Flask REST API endpoints that power the photo browsing interface
"""

import pytest
import json
import sqlite3
import tempfile
import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from server import EnhancedFlickrServer
from flask import Flask


def create_test_database_with_data(temp_path):
    """Helper to create database with test data"""
    db_path = temp_path / "flickr_metadata.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create schema
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
    
    cursor.execute("""
        CREATE TABLE photo_albums (
            photo_id TEXT,
            album_id TEXT,
            PRIMARY KEY (photo_id, album_id),
            FOREIGN KEY (photo_id) REFERENCES photos (id),
            FOREIGN KEY (album_id) REFERENCES albums (id)
        )
    """)
    
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
    
    # Insert test data
    cursor.execute("""
        INSERT INTO albums (id, title, description, photo_count, created_date, updated_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ('album1', 'Test Album 1', 'First test album', 2, '2023-01-01', '2023-01-02'))
    
    cursor.execute("""
        INSERT INTO albums (id, title, description, photo_count, created_date, updated_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ('album2', 'Test Album 2', 'Second test album', 1, '2023-02-01', '2023-02-02'))
    
    # Insert photos
    test_photos = [
        ('photo1', 'Sunset Photo', 'Beautiful sunset over the mountains', 'sunset, nature, landscape'),
        ('photo2', 'City Night', 'Downtown skyline at night', 'city, night, urban, architecture'),
        ('photo3', 'Beach Vacation', 'Relaxing day at the beach', 'beach, vacation, summer, ocean')
    ]
    
    for photo_id, title, desc, tags in test_photos:
        cursor.execute("""
            INSERT INTO photos (id, title, description, tags, date_taken, date_uploaded,
                              views, url, thumbnail_url, width, height, size, media_type,
                              license, privacy, safety_level, rotation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (photo_id, title, desc, tags, '2023-01-15', '2023-01-16', 100,
              f'https://example.com/{photo_id}.jpg', f'https://example.com/thumb_{photo_id}.jpg',
              1920, 1080, 2048000, 'photo', '0', 'public', 1, 0))
    
    # Create associations
    cursor.execute("INSERT INTO photo_albums (photo_id, album_id) VALUES (?, ?)", ('photo1', 'album1'))
    cursor.execute("INSERT INTO photo_albums (photo_id, album_id) VALUES (?, ?)", ('photo2', 'album1'))
    cursor.execute("INSERT INTO photo_albums (photo_id, album_id) VALUES (?, ?)", ('photo3', 'album2'))
    
    conn.commit()
    conn.close()
    return db_path


class TestAlbumAPI:
    """Test /api/albums endpoint"""
    
    def test_get_albums_with_data(self):
        """Test albums endpoint with populated database"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = create_test_database_with_data(temp_path)
            
            # Create thumbnails directory
            thumbnails_dir = temp_path / "thumbnails"
            thumbnails_dir.mkdir(exist_ok=True)
            
            # Create server and Flask app
            server = EnhancedFlickrServer(data_dir=str(temp_path))
            app = Flask(__name__)
            app.config['TESTING'] = True
            
            @app.route('/api/albums')
            def get_albums():
                from flask import jsonify
                try:
                    albums = server.get_albums()
                    return jsonify(albums)
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            # Test the endpoint
            client = app.test_client()
            response = client.get('/api/albums')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert isinstance(data, list)
            assert len(data) == 2
            
            # Check album structure
            album = data[0]
            required_fields = ['id', 'title', 'description', 'photo_count']
            for field in required_fields:
                assert field in album, f"Album should have {field} field"
    
    def test_albums_return_junction_table_counts(self):
        """Test that albums return correct photo counts from junction table"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = create_test_database_with_data(temp_path)
            
            # Create thumbnails directory
            thumbnails_dir = temp_path / "thumbnails"
            thumbnails_dir.mkdir(exist_ok=True)
            
            # Create server and Flask app
            server = EnhancedFlickrServer(data_dir=str(temp_path))
            app = Flask(__name__)
            app.config['TESTING'] = True
            
            @app.route('/api/albums')
            def get_albums():
                from flask import jsonify
                try:
                    albums = server.get_albums()
                    return jsonify(albums)
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            # Test the endpoint
            client = app.test_client()
            response = client.get('/api/albums')
            data = json.loads(response.data)
            
            # Find specific albums and check their counts
            album1 = next(a for a in data if a['id'] == 'album1')
            album2 = next(a for a in data if a['id'] == 'album2')
            
            assert album1['photo_count'] == 2, "Album1 should show 2 photos"
            assert album2['photo_count'] == 1, "Album2 should show 1 photo"


class TestPhotosAPI:
    """Test /api/photos endpoint"""
    
    def test_get_all_photos(self):
        """Test getting all photos without filters"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = create_test_database_with_data(temp_path)
            
            # Create thumbnails directory
            thumbnails_dir = temp_path / "thumbnails"
            thumbnails_dir.mkdir(exist_ok=True)
            
            # Create server and Flask app
            server = EnhancedFlickrServer(data_dir=str(temp_path))
            app = Flask(__name__)
            app.config['TESTING'] = True
            
            @app.route('/api/photos')
            def get_photos():
                from flask import request, jsonify
                try:
                    album_id = request.args.get('album_id')
                    search_term = request.args.get('search')
                    
                    if album_id:
                        limit = None  
                        offset = 0
                    else:
                        limit = int(request.args.get('limit', 1000))
                        offset = int(request.args.get('offset', 0))
                    
                    photos = server.get_photos(album_id, search_term, limit, offset)
                    return jsonify(photos)
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            # Test the endpoint
            client = app.test_client()
            response = client.get('/api/photos')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert isinstance(data, list)
            assert len(data) == 3
            
            # Check photo structure
            photo = data[0]
            required_fields = ['id', 'title', 'description', 'tags', 'date_taken']
            for field in required_fields:
                assert field in photo, f"Photo should have {field} field"
    
    def test_get_photos_by_album(self):
        """Test filtering photos by album"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = create_test_database_with_data(temp_path)
            
            # Create thumbnails directory
            thumbnails_dir = temp_path / "thumbnails"
            thumbnails_dir.mkdir(exist_ok=True)
            
            # Create server and Flask app
            server = EnhancedFlickrServer(data_dir=str(temp_path))
            app = Flask(__name__)
            app.config['TESTING'] = True
            
            @app.route('/api/photos')
            def get_photos():
                from flask import request, jsonify
                try:
                    album_id = request.args.get('album_id')
                    search_term = request.args.get('search')
                    
                    if album_id:
                        limit = None  
                        offset = 0
                    else:
                        limit = int(request.args.get('limit', 1000))
                        offset = int(request.args.get('offset', 0))
                    
                    photos = server.get_photos(album_id, search_term, limit, offset)
                    return jsonify(photos)
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            # Test the endpoint
            client = app.test_client()
            
            # Get photos from album1
            response = client.get('/api/photos?album_id=album1')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert len(data) == 2
            
            photo_ids = [p['id'] for p in data]
            assert 'photo1' in photo_ids
            assert 'photo2' in photo_ids
            
            # Get photos from album2
            response = client.get('/api/photos?album_id=album2')
            data = json.loads(response.data)
            assert len(data) == 1
            assert data[0]['id'] == 'photo3'
    
    def test_get_photos_with_search(self):
        """Test photo search functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = create_test_database_with_data(temp_path)
            
            # Create thumbnails directory
            thumbnails_dir = temp_path / "thumbnails"
            thumbnails_dir.mkdir(exist_ok=True)
            
            # Create server and Flask app
            server = EnhancedFlickrServer(data_dir=str(temp_path))
            app = Flask(__name__)
            app.config['TESTING'] = True
            
            @app.route('/api/photos')
            def get_photos():
                from flask import request, jsonify
                try:
                    album_id = request.args.get('album_id')
                    search_term = request.args.get('search')
                    
                    if album_id:
                        limit = None  
                        offset = 0
                    else:
                        limit = int(request.args.get('limit', 1000))
                        offset = int(request.args.get('offset', 0))
                    
                    photos = server.get_photos(album_id, search_term, limit, offset)
                    return jsonify(photos)
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            # Test the endpoint
            client = app.test_client()
            
            # Search by title
            response = client.get('/api/photos?search=Sunset')
            data = json.loads(response.data)
            assert len(data) == 1
            assert data[0]['id'] == 'photo1'
            
            # Search by description
            response = client.get('/api/photos?search=night')
            data = json.loads(response.data)
            assert len(data) == 1
            assert data[0]['id'] == 'photo2'
            
            # Search by tags
            response = client.get('/api/photos?search=nature')
            data = json.loads(response.data)
            assert len(data) == 1
            assert data[0]['id'] == 'photo1'


class TestAPIErrorHandling:
    """Test API error handling and edge cases"""
    
    def test_photos_invalid_album_id(self):
        """Test behavior with invalid album ID"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = create_test_database_with_data(temp_path)
            
            # Create thumbnails directory
            thumbnails_dir = temp_path / "thumbnails"
            thumbnails_dir.mkdir(exist_ok=True)
            
            # Create server and Flask app
            server = EnhancedFlickrServer(data_dir=str(temp_path))
            app = Flask(__name__)
            app.config['TESTING'] = True
            
            @app.route('/api/photos')
            def get_photos():
                from flask import request, jsonify
                try:
                    album_id = request.args.get('album_id')
                    search_term = request.args.get('search')
                    
                    if album_id:
                        limit = None  
                        offset = 0
                    else:
                        limit = int(request.args.get('limit', 1000))
                        offset = int(request.args.get('offset', 0))
                    
                    photos = server.get_photos(album_id, search_term, limit, offset)
                    return jsonify(photos)
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            # Test the endpoint
            client = app.test_client()
            response = client.get('/api/photos?album_id=nonexistent')
            assert response.status_code == 200  # Should not error
            
            data = json.loads(response.data)
            assert len(data) == 0  # Should return empty results
    
    def test_photos_case_insensitive_search(self):
        """Test case insensitive search"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = create_test_database_with_data(temp_path)
            
            # Create thumbnails directory
            thumbnails_dir = temp_path / "thumbnails"
            thumbnails_dir.mkdir(exist_ok=True)
            
            # Create server and Flask app
            server = EnhancedFlickrServer(data_dir=str(temp_path))
            app = Flask(__name__)
            app.config['TESTING'] = True
            
            @app.route('/api/photos')
            def get_photos():
                from flask import request, jsonify
                try:
                    album_id = request.args.get('album_id')
                    search_term = request.args.get('search')
                    
                    if album_id:
                        limit = None  
                        offset = 0
                    else:
                        limit = int(request.args.get('limit', 1000))
                        offset = int(request.args.get('offset', 0))
                    
                    photos = server.get_photos(album_id, search_term, limit, offset)
                    return jsonify(photos)
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            # Test the endpoint
            client = app.test_client()
            
            # Different cases should return same results
            response1 = client.get('/api/photos?search=SUNSET')
            response2 = client.get('/api/photos?search=sunset') 
            response3 = client.get('/api/photos?search=Sunset')
            
            data1 = json.loads(response1.data)
            data2 = json.loads(response2.data)
            data3 = json.loads(response3.data)
            
            assert len(data1) == 1
            assert len(data2) == 1
            assert len(data3) == 1
            assert data1[0]['id'] == data2[0]['id'] == data3[0]['id']
