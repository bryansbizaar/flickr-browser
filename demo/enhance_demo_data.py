#!/usr/bin/env python3
"""
Enhanced Demo Data Generator with Rich Metadata
Creates realistic photo data that looks great in the photo detail modal
"""

import sqlite3
import requests
import random
from pathlib import Path
from datetime import datetime, timedelta
import time
from faker import Faker

class EnhancedDemoDataGenerator:
    def __init__(self, output_dir="data"):
        self.output_dir = Path(output_dir)
        self.db_path = self.output_dir / "flickr_metadata.db"
        self.thumbnails_dir = self.output_dir / "thumbnails"
        
        # Create directories
        self.output_dir.mkdir(exist_ok=True)
        self.thumbnails_dir.mkdir(exist_ok=True)
        
        # Initialize faker
        self.fake = Faker()
        
        # Enhanced photo categories with richer metadata
        self.photo_categories = [
            {
                "name": "nature", 
                "keywords": ["landscape", "sunset", "mountain", "forest", "wildlife", "scenic"],
                "titles": [
                    "Golden Hour at the Lake", "Morning Mist in the Forest", "Sunset Over the Mountains",
                    "Wildlife in Their Natural Habitat", "Peaceful Morning by the River", 
                    "Autumn Colors in Full Display", "Rocky Mountain Vista", "Serene Lake Reflection"
                ],
                "descriptions": [
                    "Captured during the golden hour when the light was absolutely perfect.",
                    "This scene took my breath away - nature at its finest.",
                    "Waited for hours to get this shot, totally worth it!",
                    "The colors were even more vibrant in person.",
                    "One of those moments where you just have to stop and appreciate the beauty.",
                    "Early morning hike rewarded with this incredible view."
                ]
            },
            {
                "name": "city",
                "keywords": ["architecture", "urban", "street", "building", "skyline", "modern"],
                "titles": [
                    "Downtown Skyline at Dusk", "Street Art Discovery", "Modern Architecture Marvel",
                    "Busy City Intersection", "Historic Building Details", "Urban Sunset Reflection",
                    "City Lights After Dark", "Architectural Geometry"
                ],
                "descriptions": [
                    "The city comes alive as the sun sets and lights begin to twinkle.",
                    "Found this amazing street art in an unexpected place.",
                    "The contrast between old and new architecture tells a story.",
                    "Love the energy and movement of city life.",
                    "Details like these make urban exploration so rewarding.",
                    "Sometimes the best shots are right in your own neighborhood."
                ]
            },
            {
                "name": "food",
                "keywords": ["delicious", "homemade", "restaurant", "cooking", "fresh", "artisanal"],
                "titles": [
                    "Homemade Sourdough Success", "Farm-to-Table Perfection", "Weekend Brunch Special",
                    "Artisanal Coffee and Pastry", "Fresh Market Vegetables", "Dinner Party Centerpiece",
                    "Local Restaurant Discovery", "Seasonal Ingredient Celebration"
                ],
                "descriptions": [
                    "Finally nailed the perfect sourdough recipe after months of practice!",
                    "Nothing beats fresh, local ingredients prepared with care.",
                    "Sunday brunch with friends - food tastes better when shared.",
                    "That perfect pairing of great coffee and fresh pastry.",
                    "Stopped by the farmer's market - these colors are incredible.",
                    "Cooking for friends is one of life's great pleasures."
                ]
            },
            {
                "name": "travel",
                "keywords": ["adventure", "vacation", "explore", "destination", "journey", "discovery"],
                "titles": [
                    "Unexpected Beach Discovery", "Mountain Trail Adventure", "Historic Town Square",
                    "Local Culture Experience", "Hidden Gem Location", "Scenic Route Surprise",
                    "Memorable Journey Moment", "Travel Photography Gold"
                ],
                "descriptions": [
                    "Sometimes the best discoveries happen when you least expect them.",
                    "Every step of this hike was worth it for this view.",
                    "Love stumbling upon these charming historic places.",
                    "Travel isn't just about the destination, it's about the experiences.",
                    "Found this place completely by accident - what a lucky find!",
                    "These are the moments that make every trip memorable."
                ]
            },
            {
                "name": "people",
                "keywords": ["family", "friends", "celebration", "portrait", "memories", "togetherness"],
                "titles": [
                    "Family Reunion Joy", "Birthday Celebration Fun", "Graduation Day Pride",
                    "Friends Weekend Getaway", "Holiday Traditions", "Candid Laughter Moment",
                    "Three Generations Together", "Wedding Day Happiness"
                ],
                "descriptions": [
                    "These family moments are what life is all about.",
                    "The laughter and joy in this photo says it all.",
                    "So proud of this achievement - we had to celebrate!",
                    "Friends like these make every adventure better.",
                    "Some traditions never get old, and I love that.",
                    "Caught this perfect candid moment of pure happiness."
                ]
            },
            {
                "name": "art",
                "keywords": ["creative", "artistic", "design", "inspiration", "gallery", "expression"],
                "titles": [
                    "Local Gallery Opening Night", "Street Art Masterpiece", "Creative Workshop Results",
                    "Artistic Detail Study", "Color and Light Experiment", "Creative Process Documentation",
                    "Art Installation Discovery", "Design Inspiration Moment"
                ],
                "descriptions": [
                    "The local art scene continues to amaze and inspire.",
                    "When creativity meets opportunity, magic happens.",
                    "Learning new techniques and pushing creative boundaries.",
                    "Sometimes it's the small details that speak the loudest.",
                    "Experimenting with light and shadow to create mood.",
                    "Art has this amazing ability to make you see things differently."
                ]
            }
        ]
        
        # Enhanced album templates with richer descriptions
        self.album_templates = [
            {
                "title": "Summer Vacation 2023", 
                "desc": "Our incredible two-week adventure exploring coastal towns, hidden beaches, and local culture. Every day brought new discoveries and unforgettable moments.",
                "category": "travel", 
                "count": 45
            },
            {
                "title": "Family Gathering", 
                "desc": "Annual family reunion celebrating three generations coming together. Birthday parties, shared meals, and countless memories made.",
                "category": "people", 
                "count": 32
            },
            {
                "title": "Nature Photography", 
                "desc": "Weekend hiking adventures and landscape photography sessions. Capturing the beauty of changing seasons and wildlife in their natural habitat.",
                "category": "nature", 
                "count": 67
            },
            {
                "title": "City Architecture", 
                "desc": "Urban exploration documenting the fascinating contrast between historic buildings and modern architectural marvels throughout the city.",
                "category": "city", 
                "count": 28
            },
            {
                "title": "Food Adventures", 
                "desc": "Culinary journey through local restaurants, farmer's markets, and home cooking experiments. Every meal tells a story.",
                "category": "food", 
                "count": 39
            },
            {
                "title": "Art Gallery Visit", 
                "desc": "Contemporary art exhibition featuring local and international artists. Inspiring works that challenge perspective and ignite creativity.",
                "category": "art", 
                "count": 24
            },
            {
                "title": "Weekend Getaway", 
                "desc": "Spontaneous mountain retreat filled with hiking, campfires, and disconnecting from the digital world to reconnect with nature.",
                "category": "travel", 
                "count": 51
            },
            {
                "title": "Home Projects", 
                "desc": "DIY renovations and creative home improvement projects. Documenting the transformation from concept to completion.",
                "category": "art", 
                "count": 18
            },
            {
                "title": "Pet Photos", 
                "desc": "Our beloved furry family members in their daily adventures. From playful moments to peaceful naps, capturing their unique personalities.",
                "category": "people", 
                "count": 43
            },
            {
                "title": "Seasonal Changes", 
                "desc": "A year-long project documenting the transformation of our neighborhood through all four seasons. Same locations, different moods.",
                "category": "nature", 
                "count": 72
            }
        ]
    
    def generate_rich_photo_metadata(self, photo_id, category):
        """Generate realistic, rich metadata for a photo"""
        category_info = next(c for c in self.photo_categories if c['name'] == category)
        
        # Pick realistic title and description
        title = random.choice(category_info['titles'])
        description = random.choice(category_info['descriptions'])
        
        # Generate realistic dates (date_taken before date_uploaded)
        date_taken = self.fake.date_between(start_date='-2y', end_date='-1d')
        date_uploaded = self.fake.date_between(start_date=date_taken, end_date='today')
        
        # Generate realistic view count (some photos are more popular)
        views = random.choices(
            [random.randint(5, 50), random.randint(51, 200), random.randint(201, 1000)],
            weights=[60, 30, 10]
        )[0]
        
        # Generate realistic tags
        base_keywords = category_info['keywords']
        additional_tags = [
            'photography', 'memories', 'beautiful', 'amazing', 'perfect', 
            'love', 'incredible', 'stunning', 'moment', 'capture'
        ]
        
        # Select 3-5 tags
        selected_tags = random.sample(base_keywords, random.randint(2, 3))
        selected_tags.extend(random.sample(additional_tags, random.randint(1, 2)))
        tags = ', '.join(selected_tags)
        
        return {
            'title': title,
            'description': description,
            'date_taken': date_taken.strftime('%Y-%m-%d'),
            'date_uploaded': date_uploaded.strftime('%Y-%m-%d'),
            'views': views,
            'tags': tags
        }
    
    def update_existing_photos_with_rich_metadata(self):
        """Update existing photos with richer metadata"""
        print("🔄 Updating existing photos with rich metadata...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all photos with their associated albums to determine category
        cursor.execute("""
            SELECT DISTINCT p.id, a.title as album_title
            FROM photos p
            JOIN photo_albums pa ON p.id = pa.photo_id  
            JOIN albums a ON pa.album_id = a.id
        """)
        
        photo_album_map = {}
        for photo_id, album_title in cursor.fetchall():
            if photo_id not in photo_album_map:
                photo_album_map[photo_id] = album_title
        
        # Update each photo
        updated_count = 0
        for photo_id, album_title in photo_album_map.items():
            # Determine category from album title
            category = 'nature'  # default
            for template in self.album_templates:
                if template['title'] == album_title:
                    category = template['category']
                    break
            
            # Generate rich metadata
            metadata = self.generate_rich_photo_metadata(photo_id, category)
            
            # Update the photo
            cursor.execute("""
                UPDATE photos 
                SET title = ?, description = ?, date_taken = ?, 
                    date_uploaded = ?, views = ?, tags = ?
                WHERE id = ?
            """, (
                metadata['title'], metadata['description'], metadata['date_taken'],
                metadata['date_uploaded'], metadata['views'], metadata['tags'], photo_id
            ))
            
            updated_count += 1
            if updated_count % 50 == 0:
                print(f"  Updated {updated_count} photos...")
        
        conn.commit()
        conn.close()
        print(f"✅ Updated {updated_count} photos with rich metadata")
    
    def enhance_existing_demo_data(self):
        """Enhance existing demo data with richer metadata"""
        print("🚀 Enhancing existing demo data...")
        print("=" * 50)
        
        # Check if database exists
        if not self.db_path.exists():
            print("❌ No existing database found. Run demo data generator first.")
            return
        
        # Update photos with rich metadata
        self.update_existing_photos_with_rich_metadata()
        
        # Generate some additional comments with variety
        self.generate_enhanced_comments()
        
        print("=" * 50)
        print("🎉 Demo data enhancement complete!")
        
        # Show summary
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM photos WHERE title != 'No title' AND description != 'No description'")
        rich_photos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comments")
        total_comments = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"📊 Enhanced Data Summary:")
        print(f"   Photos with rich metadata: {rich_photos}")
        print(f"   Total comments: {total_comments}")
    
    def generate_enhanced_comments(self):
        """Generate more realistic and varied comments"""
        print("💬 Adding enhanced comments...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete old generic comments
        cursor.execute("DELETE FROM comments")
        
        # Get all photo IDs
        cursor.execute("SELECT id, title FROM photos")
        photos = cursor.fetchall()
        
        # Realistic comment templates
        comment_templates = [
            "Absolutely stunning shot!", "This is incredible!", "Love the composition!",
            "The colors are amazing!", "Perfect timing!", "Beautiful capture!",
            "This takes my breath away!", "Such great detail!", "Wonderful perspective!",
            "This is art!", "Amazing work!", "So peaceful and serene.",
            "The lighting is perfect!", "This made my day!", "Gorgeous!",
            "I need to visit this place!", "How did you get this shot?", 
            "The mood in this photo is incredible.", "This deserves to be framed!",
            "You have a great eye for photography.", "This brings back memories.",
            "Nature at its finest!", "The detail is incredible.", "Love this!",
            "This photo tells a story.", "Absolutely beautiful work!",
            "The colors just pop!", "This is wallpaper worthy!",
            "Such a peaceful moment captured.", "This is why I love photography.",
            "The composition is flawless.", "This gives me wanderlust!"
        ]
        
        comment_id = 1
        for photo_id, photo_title in photos:
            # Random number of comments (0-4, weighted toward fewer)
            num_comments = random.choices([0, 1, 2, 3, 4], weights=[25, 35, 25, 10, 5])[0]
            
            for _ in range(num_comments):
                comment_text = random.choice(comment_templates)
                author_name = self.fake.name()
                comment_date = self.fake.date_between(start_date='-1y', end_date='today')
                
                cursor.execute("""
                    INSERT INTO comments (id, photo_id, author_name, comment_text, comment_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (f"comment_{comment_id:06d}", photo_id, author_name, 
                      comment_text, comment_date.strftime('%Y-%m-%d')))
                
                comment_id += 1
        
        conn.commit()
        conn.close()
        print(f"✅ Added {comment_id-1} enhanced comments")

if __name__ == "__main__":
    enhancer = EnhancedDemoDataGenerator()
    enhancer.enhance_existing_demo_data()
