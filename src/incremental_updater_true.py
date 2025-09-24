#!/usr/bin/env python3
"""
Comprehensive Flickr Updater
Checks BOTH photostream AND albums to catch everything new
"""

import os
import json
import sys
import sqlite3
from pathlib import Path
from datetime import datetime
import time

# Add the current directory to path
sys.path.append(os.path.dirname(__file__))

try:
    from oauth_downloader import FlickrDownloaderOAuth
except ImportError:
    print("ERROR: Could not import oauth_downloader", file=sys.stderr)
    sys.exit(1)

class ComprehensiveFlickrUpdater(FlickrDownloaderOAuth):
    """Updater that checks both photostream AND albums"""
    
    def __init__(self, api_key, api_secret, user_id, output_dir="data"):
        super().__init__(api_key, api_secret, user_id, output_dir)
        self.new_photos_count = 0
        self.new_associations_count = 0
        self.skipped_photos_count = 0
        self.photostream_new_count = 0
        self.existing_photo_ids = self.get_existing_photo_ids()
        self.ensure_junction_table()
        
    def ensure_junction_table(self):
        """Ensure the junction table exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS photo_albums (
                photo_id TEXT,
                album_id TEXT,
                is_primary INTEGER DEFAULT 0,
                date_added TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (photo_id, album_id),
                FOREIGN KEY (photo_id) REFERENCES photos (id),
                FOREIGN KEY (album_id) REFERENCES albums (id)
            )
        """)
        
        conn.commit()
        conn.close()
        
    def get_existing_photo_ids(self):
        """Get set of all photo IDs already in database"""
        if not self.db_path.exists():
            print("📄 No existing database found - this will be a full download")
            return set()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM photos")
            existing_ids = {row[0] for row in cursor.fetchall()}
            conn.close()
            
            print(f"📊 Found {len(existing_ids)} existing photos in database")
            return existing_ids
            
        except Exception as e:
            print(f"⚠️ Warning: Could not read existing photos: {e}")
            return set()
    
    def get_recent_photostream_photos(self, days_back=90):
        """Get recent photos from user's photostream (not just albums)"""
        print(f"🔍 Checking photostream for photos uploaded in last {days_back} days...")
        
        all_photos = []
        page = 1
        per_page = 500
        
        while True:
            try:
                result = self.api_call(
                    'flickr.people.getPhotos',
                    user_id=self.user_id,
                    page=page,
                    per_page=per_page,
                    extras='date_upload,date_taken,tags,views,url_t,url_o'
                )
                
                if result['stat'] != 'ok':
                    print(f"❌ Error getting photostream: {result.get('message', 'Unknown error')}")
                    break
                
                photos = result['photos']['photo']
                if not photos:
                    break
                
                all_photos.extend(photos)
                
                print(f"   📄 Page {page}: Got {len(photos)} photos")
                
                # Check if we have all photos
                total_photos = int(result['photos']['total'])
                pages_total = int(result['photos']['pages'])
                
                if page >= pages_total:
                    break
                
                page += 1
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Error getting photostream page {page}: {e}")
                break
        
        # Filter for truly new photos
        new_photos = [photo for photo in all_photos if not self.photo_exists(photo['id'])]
        
        print(f"📊 Total photostream photos: {len(all_photos)}")
        print(f"🆕 New photostream photos: {len(new_photos)}")
        
        return new_photos
    
    def save_photo_metadata_standalone(self, photo_data, thumbnail_path):
        """Save photo metadata without album association (for photostream-only photos)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        photo_id = str(photo_data['id'])
        
        # Convert data safely (same as before)
        tags = ''
        if 'tags' in photo_data:
            tags_data = photo_data['tags']
            if isinstance(tags_data, dict):
                tags = tags_data.get('_content', '')
            elif isinstance(tags_data, list):
                tags = ', '.join(str(tag) for tag in tags_data)
            else:
                tags = str(tags_data)
        
        description = ''
        if 'description' in photo_data:
            if isinstance(photo_data['description'], dict):
                description = photo_data['description'].get('_content', '')
            else:
                description = str(photo_data['description'])
        
        title = ''
        if 'title' in photo_data:
            if isinstance(photo_data['title'], dict):
                title = photo_data['title'].get('_content', '')
            else:
                title = str(photo_data['title'])
        
        filename = f"{photo_data['id']}.jpg"
        thumbnail_path = str(thumbnail_path) if thumbnail_path else ''
        date_taken = str(photo_data.get('datetaken', ''))
        date_uploaded = str(photo_data.get('dateupload', ''))
        views = int(photo_data.get('views', 0)) if photo_data.get('views') else 0
        url_original = str(photo_data.get('url_o', ''))
        url_thumbnail = str(photo_data.get('url_t', ''))
        
        # Insert photo without album association
        cursor.execute("""
            INSERT OR REPLACE INTO photos 
            (id, title, description, filename, thumbnail_path, 
             date_taken, date_uploaded, views, tags, url_original, url_thumbnail)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            photo_id, title, description, filename, thumbnail_path,
            date_taken, date_uploaded, views, tags, url_original, url_thumbnail
        ))
        
        conn.commit()
        conn.close()
    
    def save_photo_metadata_junction(self, photo_data, album_id, thumbnail_path):
        """Save photo metadata with album association"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        photo_id = str(photo_data['id'])
        
        # Save photo first (same as standalone)
        self.save_photo_metadata_standalone(photo_data, thumbnail_path)
        
        # Add album association
        cursor.execute("""
            INSERT OR IGNORE INTO photo_albums (photo_id, album_id, is_primary, date_added)
            VALUES (?, ?, 1, ?)
        """, (photo_id, album_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def download_photostream_photo(self, photo):
        """Download a new photo from photostream"""
        photo_id = photo['id']
        
        if self.photo_exists(photo_id):
            return False
        
        print(f"🆕 Downloading photostream photo: {photo.get('title', 'Untitled')}")
        
        # Get detailed photo info
        photo_info = self.get_photo_info(photo_id)
        if photo_info:
            photo.update(photo_info)
        
        # Download thumbnail
        thumbnail_path = None
        thumbnail_url = photo.get('url_t')
        if thumbnail_url:
            thumbnail_path = self.download_thumbnail(photo_id, thumbnail_url)
        
        # Get comments
        comments = self.get_photo_comments(photo_id)
        self.save_comments(photo_id, comments)
        
        # Save photo metadata (without album association)
        self.save_photo_metadata_standalone(photo, thumbnail_path)
        
        # Add to existing set
        self.existing_photo_ids.add(photo_id)
        self.photostream_new_count += 1
        self.new_photos_count += 1
        
        return True
    
    def photo_exists(self, photo_id):
        """Check if photo already exists in database"""
        return photo_id in self.existing_photo_ids
    
    def photo_in_album(self, photo_id, album_id):
        """Check if photo is already associated with album"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM photo_albums WHERE photo_id = ? AND album_id = ?", (photo_id, album_id))
        exists = cursor.fetchone() is not None
        
        conn.close()
        return exists
    
    def download_album_photo(self, photo, album_id, album_title):
        """Download/associate photo with album"""
        photo_id = photo['id']
        
        photo_exists = self.photo_exists(photo_id)
        in_album = self.photo_in_album(photo_id, album_id) if photo_exists else False
        
        if photo_exists and in_album:
            self.skipped_photos_count += 1
            return False
        
        if not photo_exists:
            print(f"🆕 Downloading new album photo: {photo.get('title', 'Untitled')}")
            
            # Get detailed photo info
            photo_info = self.get_photo_info(photo_id)
            if photo_info:
                photo.update(photo_info)
            
            # Download thumbnail
            thumbnail_path = None
            thumbnail_url = photo.get('url_t')
            if thumbnail_url:
                thumbnail_path = self.download_thumbnail(photo_id, thumbnail_url)
            
            # Get comments
            comments = self.get_photo_comments(photo_id)
            self.save_comments(photo_id, comments)
            
            # Add to existing set
            self.existing_photo_ids.add(photo_id)
            self.new_photos_count += 1
        else:
            print(f"🔗 Adding existing photo to album: {photo.get('title', 'Untitled')}")
            thumbnail_path = None
        
        # Save with album association
        self.save_photo_metadata_junction(photo, album_id, thumbnail_path)
        
        if not in_album:
            self.new_associations_count += 1
        
        return True
    
    def update_photostream(self):
        """Check photostream for new photos not in any album"""
        print("\\n📸 CHECKING PHOTOSTREAM FOR NEW PHOTOS")
        print("=" * 50)
        
        new_photos = self.get_recent_photostream_photos()
        
        if not new_photos:
            print("✅ No new photos in photostream")
            return
        
        print(f"🔄 Processing {len(new_photos)} new photostream photos...")
        
        for i, photo in enumerate(new_photos, 1):
            try:
                self.download_photostream_photo(photo)
                if i % 10 == 0:
                    print(f"   📊 Progress: {i}/{len(new_photos)}")
            except Exception as e:
                print(f"❌ Error downloading photo {photo.get('title', 'Unknown')}: {e}")
    
    def update_albums(self):
        """Check all albums for new photos/associations"""
        print("\\n📁 CHECKING ALBUMS FOR UPDATES")
        print("=" * 50)
        
        try:
            albums = self.get_user_albums()
            print(f"📁 Found {len(albums)} albums to check")
        except Exception as e:
            print(f"❌ Error getting albums: {e}")
            return
        
        for i, album in enumerate(albums, 1):
            album_title = album['title']['_content'] if isinstance(album['title'], dict) else str(album['title'])
            print(f"\\n[{i}/{len(albums)}] {album_title}")
            
            try:
                self.update_album_incremental(album['id'], album_title)
            except Exception as e:
                print(f"❌ Error updating album '{album_title}': {e}")
                continue
    
    def update_album_incremental(self, album_id, album_title):
        """Update album with new photos/associations"""
        print(f"🔄 Checking album: {album_title}")
        
        # Get all photos in album from Flickr (with pagination)
        photos = self.get_album_photos(album_id)
        total_photos = len(photos)
        
        print(f"📊 Album has {total_photos} total photos")
        
        # Update album metadata
        self.save_album_metadata(album_id, album_title, "", total_photos)
        
        # Process all photos
        album_new_count = 0
        for photo in photos:
            if self.download_album_photo(photo, album_id, album_title):
                album_new_count += 1
        
        if album_new_count > 0:
            print(f"✅ Added {album_new_count} new items to album '{album_title}'")
        else:
            print(f"✅ Album '{album_title}' was already up to date")
    
    def comprehensive_update(self):
        """Perform comprehensive update: photostream + albums"""
        print("🚀 COMPREHENSIVE FLICKR UPDATE")
        print("Checking BOTH photostream AND albums for new content")
        print("=" * 60)
        
        start_time = time.time()
        
        # Step 1: Check photostream for new photos
        self.update_photostream()
        
        # Step 2: Check albums for new associations
        self.update_albums()
        
        # Summary
        elapsed = time.time() - start_time
        print("\\n" + "=" * 60)
        print("📊 COMPREHENSIVE UPDATE SUMMARY")
        print("=" * 60)
        print(f"⏱️  Total time: {elapsed/60:.1f} minutes")
        print(f"🆕 New photos downloaded: {self.new_photos_count}")
        print(f"   - From photostream: {self.photostream_new_count}")
        print(f"   - From albums: {self.new_photos_count - self.photostream_new_count}")
        print(f"🔗 New album associations: {self.new_associations_count}")
        print(f"⏭️  Items skipped (already present): {self.skipped_photos_count}")
        print(f"📊 Total photos in database: {len(self.existing_photo_ids)}")
        
        if self.new_photos_count > 0 or self.new_associations_count > 0:
            print(f"\\n✅ Successfully updated your collection!")
            print(f"💡 New photos will appear in your browser")
        else:
            print("\\n✅ Your collection is completely up to date!")

def load_credentials():
    """Load API credentials from config file"""
    config_file = Path.home() / ".flickr_browser_config.json"
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('api_key'), config.get('api_secret'), config.get('user_id')
        except Exception as e:
            print(f"ERROR: Could not load credentials: {e}", file=sys.stderr)
            return None, None, None
    else:
        print("ERROR: No credentials found. Run the launcher first.", file=sys.stderr)
        return None, None, None

def main():
    print("🔄 Comprehensive Flickr Updater")
    print("Checks BOTH photostream AND albums")
    print("=" * 50)
    
    # Load credentials
    api_key, api_secret, user_id = load_credentials()
    
    if not all([api_key, api_secret, user_id]):
        print("❌ Missing API credentials")
        sys.exit(1)
    
    # Set up data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    try:
        # Create comprehensive updater
        print("🔗 Connecting to Flickr...")
        updater = ComprehensiveFlickrUpdater(api_key, api_secret, user_id, str(data_dir))
        
        # Check authentication
        if not updater.load_token():
            print("🔐 OAuth authentication required")
            sys.exit(2)
        
        # Test authentication
        result = updater.api_call('flickr.test.login')
        
        if result.get('stat') != 'ok':
            print("❌ Authentication failed")
            sys.exit(1)
        
        user = result.get('user', {})
        username = user.get('username', {}).get('_content', 'Unknown')
        print(f"✅ Authenticated as: {username}")
        
        # Perform comprehensive update
        updater.comprehensive_update()
        
    except KeyboardInterrupt:
        print("\\n⚠️ Update cancelled by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error during update: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
