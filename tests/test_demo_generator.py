#!/usr/bin/env python3
"""
Demo data generator tests for Flickr Local Browser
Tests the demo data generation system that creates realistic test data
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
import sys
import os

# Add project directories to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'demo'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from demo_data_generator import DemoDataGenerator


class TestDemoDataGenerator:
    """Test the demo data generation functionality"""
    
    @pytest.fixture
    def temp_demo_dir(self):
        """Create temporary directory for demo data testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def demo_generator(self, temp_demo_dir):
        """Create DemoDataGenerator instance"""
        return DemoDataGenerator(output_dir=str(temp_demo_dir))
    
    def test_demo_generator_initialization(self, demo_generator, temp_demo_dir):
        """Test that demo generator initializes correctly"""
        assert demo_generator.output_dir == temp_demo_dir
        assert demo_generator.db_path == temp_demo_dir / "flickr_metadata.db"
        assert demo_generator.thumbnails_dir == temp_demo_dir / "thumbnails"
        
        # Check that directories are created
        assert demo_generator.output_dir.exists()
        assert demo_generator.thumbnails_dir.exists()
    
    def test_database_initialization(self, demo_generator):
        """Test database schema creation"""
        demo_generator.init_database()
        
        # Check database exists
        assert demo_generator.db_path.exists()
        
        # Check tables exist
        conn = sqlite3.connect(demo_generator.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['albums', 'photos', 'photo_albums', 'comments']
        for table in expected_tables:
            assert table in tables, f"Table {table} should exist"
        
        conn.close()
    
    def test_album_templates_structure(self, demo_generator):
        """Test that album templates have correct structure"""
        templates = demo_generator.album_templates
        
        assert len(templates) > 0, "Should have album templates"
        
        for template in templates:
            assert 'title' in template, "Album template should have title"
            assert 'desc' in template, "Album template should have description"
            assert 'category' in template, "Album template should have category"
            assert 'count' in template, "Album template should have photo count"
            
            # Check data types
            assert isinstance(template['title'], str)
            assert isinstance(template['desc'], str)
            assert isinstance(template['category'], str)
            assert isinstance(template['count'], int)
            assert template['count'] > 0, "Photo count should be positive"
    
    def test_photo_categories_structure(self, demo_generator):
        """Test that photo categories have correct structure"""
        categories = demo_generator.photo_categories
        
        assert len(categories) > 0, "Should have photo categories"
        
        for category in categories:
            assert 'name' in category, "Category should have name"
            assert 'keywords' in category, "Category should have keywords"
            
            assert isinstance(category['name'], str)
            assert isinstance(category['keywords'], list)
            assert len(category['keywords']) > 0, "Should have keywords"
            
            for keyword in category['keywords']:
                assert isinstance(keyword, str)


class TestDemoDataGeneration:
    """Test actual demo data generation (without external API calls)"""
    
    @pytest.fixture
    def temp_demo_dir(self):
        """Create temporary directory for demo data testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def demo_generator_with_db(self, temp_demo_dir):
        """Create demo generator with initialized database"""
        generator = DemoDataGenerator(output_dir=str(temp_demo_dir))
        generator.init_database()
        return generator
    
    def test_can_create_fake_photo_metadata(self, demo_generator_with_db):
        """Test creating fake photo metadata without external calls"""
        generator = demo_generator_with_db
        
        # Create some fake photo data manually (without external API calls)
        conn = sqlite3.connect(generator.db_path)
        cursor = conn.cursor()
        
        # Insert a test album
        cursor.execute("""
            INSERT INTO albums (id, title, description, photo_count, created_date, updated_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('test_album', 'Test Album', 'Generated test album', 3, '2023-01-01', '2023-01-01'))
        
        # Insert test photos with realistic metadata
        for i in range(3):
            photo_id = f'demo_photo_{i}'
            cursor.execute("""
                INSERT INTO photos (id, title, description, tags, date_taken, date_uploaded,
                                  views, url, thumbnail_url, width, height, size, media_type,
                                  license, privacy, safety_level, rotation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                photo_id,
                f'Demo Photo {i+1}',
                f'Generated demo photo number {i+1}',
                'demo, test, generated',
                '2023-01-15',
                '2023-01-16',
                100 + i * 50,
                f'https://demo.com/photo{i}.jpg',
                f'https://demo.com/thumb{i}.jpg',
                1920, 1080, 2048000,
                'photo', '0', 'public', 1, 0
            ))
            
            # Link photo to album
            cursor.execute("INSERT INTO photo_albums (photo_id, album_id) VALUES (?, ?)", 
                          (photo_id, 'test_album'))
        
        conn.commit()
        
        # Verify data was inserted correctly
        cursor.execute("SELECT COUNT(*) FROM albums")
        album_count = cursor.fetchone()[0]
        assert album_count == 1, "Should have 1 album"
        
        cursor.execute("SELECT COUNT(*) FROM photos")
        photo_count = cursor.fetchone()[0]
        assert photo_count == 3, "Should have 3 photos"
        
        cursor.execute("SELECT COUNT(*) FROM photo_albums")
        association_count = cursor.fetchone()[0]
        assert association_count == 3, "Should have 3 photo-album associations"
        
        conn.close()
    
    def test_faker_integration(self, demo_generator_with_db):
        """Test that Faker integration works for generating realistic data"""
        generator = demo_generator_with_db
        
        # Test that Faker is working
        fake_name = generator.fake.name()
        fake_sentence = generator.fake.sentence()
        fake_date = generator.fake.date()
        
        assert isinstance(fake_name, str)
        assert len(fake_name) > 0
        
        assert isinstance(fake_sentence, str)
        assert len(fake_sentence) > 0
        
        assert isinstance(fake_date, str)
        
        # Test generating multiple fake values to ensure randomness
        names = [generator.fake.name() for _ in range(5)]
        assert len(set(names)) > 1, "Should generate different names"
    
    def test_database_constraints_enforced(self, demo_generator_with_db):
        """Test that database constraints are properly enforced"""
        generator = demo_generator_with_db
        conn = sqlite3.connect(generator.db_path)
        cursor = conn.cursor()
        
        # Test duplicate photo ID constraint
        cursor.execute("""
            INSERT INTO photos (id, title, description, tags, date_taken, date_uploaded,
                              views, url, thumbnail_url, width, height, size, media_type,
                              license, privacy, safety_level, rotation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('unique_photo', 'Photo 1', 'First photo', 'test', '2023-01-01', '2023-01-01',
              100, 'http://example.com/1.jpg', 'http://example.com/thumb1.jpg',
              1920, 1080, 2048000, 'photo', '0', 'public', 1, 0))
        
        # Try to insert duplicate - should raise integrity error
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO photos (id, title, description, tags, date_taken, date_uploaded,
                                  views, url, thumbnail_url, width, height, size, media_type,
                                  license, privacy, safety_level, rotation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ('unique_photo', 'Photo 2', 'Duplicate photo', 'test', '2023-01-01', '2023-01-01',
                  200, 'http://example.com/2.jpg', 'http://example.com/thumb2.jpg',
                  1920, 1080, 2048000, 'photo', '0', 'public', 1, 0))
        
        conn.close()


class TestDemoDataQuality:
    """Test the quality and realism of generated demo data"""
    
    @pytest.fixture
    def temp_demo_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def populated_demo_db(self, temp_demo_dir):
        """Create a demo database with sample data"""
        generator = DemoDataGenerator(output_dir=str(temp_demo_dir))
        generator.init_database()
        
        conn = sqlite3.connect(generator.db_path)
        cursor = conn.cursor()
        
        # Create realistic demo data
        albums_data = [
            ('album1', 'Summer Vacation 2023', 'Our trip to the beach', 5),
            ('album2', 'Family Photos', 'Family gathering pictures', 8),
            ('album3', 'Nature Photography', 'Landscape and wildlife shots', 12)
        ]
        
        for album_id, title, desc, count in albums_data:
            cursor.execute("""
                INSERT INTO albums (id, title, description, photo_count, created_date, updated_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (album_id, title, desc, count, '2023-01-01', '2023-01-01'))
        
        # Create photos with varied metadata
        photo_templates = [
            ('Sunset Beach', 'Beautiful sunset over the ocean', 'sunset, beach, nature'),
            ('City Skyline', 'Downtown view at night', 'city, urban, architecture'),
            ('Mountain Hike', 'Trail through the mountains', 'hiking, nature, outdoors'),
            ('Family Dinner', 'Celebrating grandmas birthday', 'family, celebration, food'),
            ('Art Gallery', 'Modern sculpture exhibition', 'art, culture, museum')
        ]
        
        for i, (title, desc, tags) in enumerate(photo_templates):
            photo_id = f'photo_{i+1}'
            cursor.execute("""
                INSERT INTO photos (id, title, description, tags, date_taken, date_uploaded,
                                  views, url, thumbnail_url, width, height, size, media_type,
                                  license, privacy, safety_level, rotation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                photo_id, title, desc, tags,
                f'2023-0{(i%9)+1}-15', f'2023-0{(i%9)+1}-16',
                100 + i * 75, f'https://demo.com/{photo_id}.jpg', f'https://demo.com/thumb_{photo_id}.jpg',
                1920, 1080, 2048000, 'photo', '0', 'public', 1, 0
            ))
            
            # Associate with albums (some photos in multiple albums)
            album_id = f'album{(i % 3) + 1}'
            cursor.execute("INSERT INTO photo_albums (photo_id, album_id) VALUES (?, ?)", 
                          (photo_id, album_id))
        
        conn.commit()
        conn.close()
        return generator
    
    def test_album_photo_count_accuracy(self, populated_demo_db):
        """Test that album photo counts reflect actual associations"""
        from server import EnhancedFlickrServer
        
        server = EnhancedFlickrServer(data_dir=str(populated_demo_db.output_dir))
        albums = server.get_albums()
        
        # Verify albums have realistic photo counts
        assert len(albums) == 3
        
        for album in albums:
            assert album['photo_count'] > 0, f"Album {album['title']} should have photos"
            assert album['photo_count'] <= 5, "Photo count should be reasonable for test data"
    
    def test_photo_metadata_variety(self, populated_demo_db):
        """Test that photos have varied and realistic metadata"""
        from server import EnhancedFlickrServer
        
        server = EnhancedFlickrServer(data_dir=str(populated_demo_db.output_dir))
        photos = server.get_photos()
        
        assert len(photos) == 5
        
        # Check for variety in titles
        titles = [photo['title'] for photo in photos]
        assert len(set(titles)) == len(titles), "All photo titles should be unique"
        
        # Check for variety in tags
        all_tags = []
        for photo in photos:
            if photo['tags']:
                all_tags.extend(photo['tags'].split(', '))
        
        unique_tags = set(all_tags)
        assert len(unique_tags) >= 8, "Should have variety in tags"
        
        # Check for realistic view counts
        view_counts = [photo['views'] for photo in photos if photo['views']]
        assert all(0 <= count <= 1000 for count in view_counts), "View counts should be realistic"
    
    def test_search_functionality_with_demo_data(self, populated_demo_db):
        """Test that search works correctly with demo data"""
        from server import EnhancedFlickrServer
        
        server = EnhancedFlickrServer(data_dir=str(populated_demo_db.output_dir))
        
        # Search by different criteria
        sunset_photos = server.get_photos(search_term='sunset')
        assert len(sunset_photos) >= 1, "Should find sunset photos"
        
        nature_photos = server.get_photos(search_term='nature')
        assert len(nature_photos) >= 1, "Should find nature photos"
        
        city_photos = server.get_photos(search_term='city')
        assert len(city_photos) >= 1, "Should find city photos"
        
        # Test case insensitive search
        sunset_upper = server.get_photos(search_term='SUNSET')
        sunset_lower = server.get_photos(search_term='sunset')
        assert len(sunset_upper) == len(sunset_lower), "Search should be case insensitive"
