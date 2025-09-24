#!/usr/bin/env python3
"""
Demo Data Generator for Flickr Local Browser Portfolio
Creates realistic dummy data with actual photos from free services
"""

import sqlite3
import requests
import random
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import time
from faker import Faker

class DemoDataGenerator:
    def __init__(self, output_dir="data"):
        self.output_dir = Path(output_dir)
        self.db_path = self.output_dir / "flickr_metadata.db"
        self.thumbnails_dir = self.output_dir / "thumbnails"
        
        # Create directories
        self.output_dir.mkdir(exist_ok=True)
        self.thumbnails_dir.mkdir(exist_ok=True)
        
        # Initialize faker
        self.fake = Faker()
        
        # Photo categories for realistic albums
        self.photo_categories = [
            {"name": "nature", "keywords": ["forest", "mountain", "lake", "sunset", "wildlife"]},
            {"name": "city", "keywords": ["architecture", "street", "building", "urban", "skyline"]},
            {"name": "food", "keywords": ["restaurant", "cooking", "meal", "recipe", "delicious"]},
            {"name": "travel", "keywords": ["vacation", "adventure", "explore", "journey", "destination"]},
            {"name": "people", "keywords": ["family", "friends", "portrait", "celebration", "gathering"]},
            {"name": "art", "keywords": ["creative", "design", "artistic", "gallery", "exhibition"]},
        ]
        
        # Sample album data
        self.album_templates = [
            {"title": "Summer Vacation 2023", "desc": "Our amazing trip to the coast", "category": "travel", "count": 45},
            {"title": "Family Gathering", "desc": "Birthday celebration with everyone", "category": "people", "count": 32},
            {"title": "Nature Photography", "desc": "Weekend hiking and landscape shots", "category": "nature", "count": 67},
            {"title": "City Architecture", "desc": "Urban exploration and building photography", "category": "city", "count": 28},
            {"title": "Food Adventures", "desc": "Trying new restaurants and recipes", "category": "food", "count": 39},
            {"title": "Art Gallery Visit", "desc": "Contemporary art exhibition downtown", "category": "art", "count": 24},
            {"title": "Weekend Getaway", "desc": "Short trip to the mountains", "category": "travel", "count": 51},
            {"title": "Home Projects", "desc": "DIY and home improvement photos", "category": "art", "count": 18},
            {"title": "Pet Photos", "desc": "Our furry family members", "category": "people", "count": 43},
            {"title": "Seasonal Changes", "desc": "Four seasons in our neighborhood", "category": "nature", "count": 72},
        ]
    
    def init_database(self):
        """Initialize the demo database with proper schema"""
        print("🗃️ Setting up database...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Drop existing tables to start fresh
        cursor.execute("DROP TABLE IF EXISTS comments")
        cursor.execute("DROP TABLE IF EXISTS photo_albums") 
        cursor.execute("DROP TABLE IF EXISTS photos")
        cursor.execute("DROP TABLE IF EXISTS albums")
        
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
        
        # Create photos table (without album_id for many-to-many)
        cursor.execute("""
            CREATE TABLE photos (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                filename TEXT,
                thumbnail_path TEXT,
                date_taken TEXT,
                date_uploaded TEXT,
                views INTEGER,
                tags TEXT,
                url_original TEXT,
                url_thumbnail TEXT
            )
        """)
        
        # Create junction table for many-to-many relationship
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
                author_name TEXT,
                comment_text TEXT,
                comment_date TEXT,
                FOREIGN KEY (photo_id) REFERENCES photos (id)
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Database initialized")
    
    def download_photo(self, photo_id, category="random", width=150, height=150):
        """Download a photo from Lorem Picsum or Unsplash"""
        filename = f"{photo_id}.jpg"
        filepath = self.thumbnails_dir / filename
        
        # Try Lorem Picsum first (more reliable)
        urls = [
            f"https://picsum.photos/{width}/{height}?random={photo_id}",
            f"https://source.unsplash.com/{width}x{height}/?{category}",
        ]
        
        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    print(f"📸 Downloaded {filename}")
                    return filename
            except Exception as e:
                print(f"⚠️ Failed to download from {url}: {e}")
                continue
        
        # If both fail, create a placeholder
        print(f"⚠️ Creating placeholder for {filename}")
        return self.create_placeholder(photo_id, width, height)
    
    def create_placeholder(self, photo_id, width=150, height=150):
        """Create a simple colored placeholder image"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Generate a color based on photo_id for consistency
            random.seed(photo_id)
            color = (
                random.randint(100, 255),
                random.randint(100, 255), 
                random.randint(100, 255)
            )
            
            img = Image.new('RGB', (width, height), color=color)
            draw = ImageDraw.Draw(img)
            
            # Add photo ID text
            text = f"Photo\n{photo_id[:8]}"
            bbox = draw.textbbox((0, 0), text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            draw.text((x, y), text, fill=(255, 255, 255), align="center")
            
            filename = f"{photo_id}.jpg"
            filepath = self.thumbnails_dir / filename
            img.save(filepath, 'JPEG')
            print(f"🎨 Created placeholder {filename}")
            return filename
            
        except ImportError:
            print("⚠️ PIL not available, skipping placeholder creation")
            return f"{photo_id}.jpg"
    
    def generate_albums(self):
        """Generate sample albums"""
        print("📁 Creating albums...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        albums = []
        for i, template in enumerate(self.album_templates):
            album_id = f"album_{i+1:03d}"
            
            # Add some variation to the template
            created_date = self.fake.date_between(start_date='-2y', end_date='-1m')
            updated_date = self.fake.date_between(start_date=created_date, end_date='today')
            
            album_data = {
                'id': album_id,
                'title': template['title'],
                'description': template['desc'],
                'photo_count': template['count'],
                'category': template['category'],
                'created_date': created_date.isoformat(),
                'updated_date': updated_date.isoformat()
            }
            
            cursor.execute("""
                INSERT INTO albums (id, title, description, photo_count, created_date, updated_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (album_data['id'], album_data['title'], album_data['description'], 
                  album_data['photo_count'], album_data['created_date'], album_data['updated_date']))
            
            albums.append(album_data)
            print(f"📁 Created album: {album_data['title']} ({album_data['photo_count']} photos)")
        
        conn.commit()
        conn.close()
        return albums
    
    def generate_photos_and_associations(self, albums):
        """Generate photos and create many-to-many album associations"""
        print("📸 Generating photos...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        photo_counter = 1
        
        for album in albums:
            album_id = album['id']
            category = album['category']
            target_count = album['photo_count']
            
            print(f"📸 Generating {target_count} photos for '{album['title']}'...")
            
            for i in range(target_count):
                photo_id = f"photo_{photo_counter:06d}"
                photo_counter += 1
                
                # Generate realistic metadata
                title = self.fake.catch_phrase()
                description = self.fake.sentence(nb_words=8)
                date_taken = self.fake.date_between(start_date='-2y', end_date='today')
                date_uploaded = self.fake.date_between(start_date=date_taken, end_date='today')
                views = random.randint(1, 1000)
                
                # Generate tags based on category
                category_info = next(c for c in self.photo_categories if c['name'] == category)
                tags = ', '.join(random.sample(category_info['keywords'], random.randint(2, 4)))
                
                # Download/create photo
                filename = self.download_photo(photo_id, category)
                thumbnail_path = f"thumbnails/{filename}"
                
                # Insert photo
                cursor.execute("""
                    INSERT INTO photos 
                    (id, title, description, filename, thumbnail_path, date_taken, 
                     date_uploaded, views, tags, url_original, url_thumbnail)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (photo_id, title, description, filename, thumbnail_path,
                      date_taken.isoformat(), date_uploaded.isoformat(), views, tags,
                      f"https://example.com/original/{filename}",
                      f"https://example.com/thumbnail/{filename}"))
                
                # Create album association
                cursor.execute("""
                    INSERT INTO photo_albums (photo_id, album_id)
                    VALUES (?, ?)
                """, (photo_id, album_id))
                
                # Add some photos to multiple albums (realistic overlap)
                if random.random() < 0.3:  # 30% chance of being in another album
                    other_album = random.choice([a for a in albums if a['id'] != album_id])
                    cursor.execute("""
                        INSERT OR IGNORE INTO photo_albums (photo_id, album_id)
                        VALUES (?, ?)
                    """, (photo_id, other_album['id']))
                
                # Rate limiting to be nice to free services
                if i % 10 == 0:
                    time.sleep(1)
                    print(f"  📸 Generated {i+1}/{target_count} photos...")
        
        conn.commit()
        conn.close()
        print(f"✅ Generated {photo_counter-1} photos total")
    
    def generate_comments(self):
        """Generate realistic comments for photos"""
        print("💬 Adding comments...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all photo IDs
        cursor.execute("SELECT id FROM photos")
        photo_ids = [row[0] for row in cursor.fetchall()]
        
        comment_counter = 1
        for photo_id in photo_ids:
            # Random number of comments (0-5)
            num_comments = random.choices([0, 1, 2, 3, 4, 5], weights=[30, 25, 20, 15, 7, 3])[0]
            
            for _ in range(num_comments):
                comment_id = f"comment_{comment_counter:06d}"
                author_name = self.fake.name()
                comment_text = random.choice([
                    "Great shot!",
                    "Beautiful photo!",
                    "Love this perspective",
                    "Amazing colors",
                    "Nice composition!",
                    "Stunning!",
                    "This is fantastic",
                    "Wonderful capture",
                    "Really nice work",
                    "Perfect timing!"
                ])
                comment_date = self.fake.date_between(start_date='-1y', end_date='today')
                
                cursor.execute("""
                    INSERT INTO comments (id, photo_id, author_name, comment_text, comment_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (comment_id, photo_id, author_name, comment_text, comment_date.isoformat()))
                
                comment_counter += 1
        
        conn.commit()
        conn.close()
        print(f"✅ Added {comment_counter-1} comments")
    
    def generate_all(self):
        """Generate complete demo dataset"""
        print("🚀 Starting demo data generation...")
        print("=" * 50)
        
        # Initialize database
        self.init_database()
        
        # Generate albums
        albums = self.generate_albums()
        
        # Generate photos and associations
        self.generate_photos_and_associations(albums)
        
        # Generate comments
        self.generate_comments()
        
        print("=" * 50)
        print("🎉 Demo data generation complete!")
        print(f"📁 Database: {self.db_path}")
        print(f"📸 Thumbnails: {self.thumbnails_dir}")
        
        # Print summary
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM albums")
        album_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM photos")
        photo_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comments")
        comment_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM photo_albums")
        association_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"📊 Summary:")
        print(f"   Albums: {album_count}")
        print(f"   Photos: {photo_count}")
        print(f"   Comments: {comment_count}")
        print(f"   Photo-Album associations: {association_count}")

if __name__ == "__main__":
    generator = DemoDataGenerator()
    generator.generate_all()