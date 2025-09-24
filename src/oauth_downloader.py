#!/usr/bin/env python3
"""
Flickr Album Downloader with OAuth Authentication
Downloads all Flickr albums (public and private) with photos, thumbnails, and metadata
"""

import os
import json
import requests
import sqlite3
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import argparse
from pathlib import Path
import webbrowser
import hashlib
import hmac
import base64
import time
import urllib.parse

class FlickrDownloaderOAuth:
    def __init__(self, api_key, api_secret, user_id, output_dir="data"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.user_id = user_id
        self.output_dir = Path(output_dir)
        self.base_url = "https://www.flickr.com/services/rest/"
        self.token_file = Path.home() / ".flickr_token"
        
        self.oauth_token = None
        self.oauth_token_secret = None
        
        # Create output directory structure
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "thumbnails").mkdir(exist_ok=True)
        
        # Initialize database
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for metadata storage"""
        self.db_path = self.output_dir / "flickr_metadata.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables (same as before)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS albums (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                photo_count INTEGER,
                created_date TEXT,
                updated_date TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS photos (
                id TEXT PRIMARY KEY,
                album_id TEXT,
                title TEXT,
                description TEXT,
                filename TEXT,
                thumbnail_path TEXT,
                date_taken TEXT,
                date_uploaded TEXT,
                views INTEGER,
                tags TEXT,
                url_original TEXT,
                url_thumbnail TEXT,
                FOREIGN KEY (album_id) REFERENCES albums (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                photo_id TEXT,
                author TEXT,
                comment TEXT,
                date_created TEXT,
                FOREIGN KEY (photo_id) REFERENCES photos (id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def load_token(self):
        """Load OAuth token from file"""
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    token_data = json.load(f)
                    self.oauth_token = token_data.get('oauth_token')
                    self.oauth_token_secret = token_data.get('oauth_token_secret')
                    print("✅ Loaded existing OAuth token")
                    return True
            except Exception as e:
                print(f"Error loading token: {e}")
        return False
    
    def save_token(self):
        """Save OAuth token to file"""
        token_data = {
            'oauth_token': self.oauth_token,
            'oauth_token_secret': self.oauth_token_secret
        }
        with open(self.token_file, 'w') as f:
            json.dump(token_data, f)
        print("✅ Saved OAuth token")
    
    def generate_signature(self, method, url, params):
        """Generate OAuth signature"""
        # Create signature base string
        normalized_params = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        signature_base = f"{method.upper()}&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(normalized_params, safe='')}"
        
        # Create signing key
        signing_key = f"{urllib.parse.quote(self.api_secret, safe='')}&{urllib.parse.quote(self.oauth_token_secret or '', safe='')}"
        
        # Generate signature
        signature = base64.b64encode(
            hmac.new(signing_key.encode(), signature_base.encode(), hashlib.sha1).digest()
        ).decode()
        
        return signature
    
    def oauth_request(self, method, url, params=None):
        """Make OAuth authenticated request"""
        if params is None:
            params = {}
        
        # Add OAuth parameters
        oauth_params = {
            'oauth_consumer_key': self.api_key,
            'oauth_nonce': str(int(time.time())),
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_version': '1.0'
        }
        
        if self.oauth_token:
            oauth_params['oauth_token'] = self.oauth_token
        
        # Combine all parameters
        all_params = {**params, **oauth_params}
        
        # Generate signature
        signature = self.generate_signature(method, url, all_params)
        oauth_params['oauth_signature'] = signature
        
        # Make request
        if method.upper() == 'GET':
            response = requests.get(url, params={**params, **oauth_params})
        else:
            response = requests.post(url, data={**params, **oauth_params})
        
        return response
    
    def authenticate(self):
        """Perform OAuth authentication"""
        print("🔐 Starting OAuth authentication...")
        
        # Step 1: Get request token
        response = self.oauth_request('GET', 'https://www.flickr.com/services/oauth/request_token', 
                                     {'oauth_callback': 'oob'})
        
        if response.status_code != 200:
            raise Exception(f"Failed to get request token: {response.text}")
        
        token_data = dict(parse_qs(response.text))
        self.oauth_token = token_data['oauth_token'][0]
        self.oauth_token_secret = token_data['oauth_token_secret'][0]
        
        # Step 2: User authorization
        auth_url = f"https://www.flickr.com/services/oauth/authorize?oauth_token={self.oauth_token}&perms=read"
        print(f"\n📱 Please visit this URL to authorize the application:")
        print(f"   {auth_url}")
        print("\n🔑 After authorizing, you'll get a verification code.")
        
        # Try to open browser automatically
        try:
            webbrowser.open(auth_url)
            print("✅ Opened authorization URL in your browser")
        except:
            print("❌ Could not open browser automatically")
        
        verification_code = input("\n🔢 Enter the verification code: ").strip()
        
        # Step 3: Get access token
        response = self.oauth_request('GET', 'https://www.flickr.com/services/oauth/access_token',
                                     {'oauth_verifier': verification_code})
        
        if response.status_code != 200:
            raise Exception(f"Failed to get access token: {response.text}")
        
        token_data = dict(parse_qs(response.text))
        self.oauth_token = token_data['oauth_token'][0]
        self.oauth_token_secret = token_data['oauth_token_secret'][0]
        
        self.save_token()
        print("🎉 Authentication successful!")
    
    def api_call(self, method, **params):
        """Make authenticated API call to Flickr"""
        params.update({
            'method': method,
            'format': 'json',
            'nojsoncallback': 1
        })
        
        response = self.oauth_request('GET', self.base_url, params)
        response.raise_for_status()
        return response.json()
    
    def get_user_albums(self):
        """Get all albums for the user with pagination"""
        print("Fetching user albums...")
        albums = []
        page = 1
        per_page = 500
        
        while True:
            result = self.api_call(
                'flickr.photosets.getList', 
                user_id=self.user_id,
                page=page,
                per_page=per_page
            )
            
            if result['stat'] != 'ok':
                raise Exception(f"API Error: {result.get('message', 'Unknown error')}")
            
            page_albums = result['photosets']['photoset']
            albums.extend(page_albums)
            
            print(f"Fetched page {page} with {len(page_albums)} albums")
            
            if page >= result['photosets']['pages']:
                break
            
            page += 1
        
        print(f"Total albums found: {len(albums)}")
        return albums
    
    def get_album_photos(self, album_id):
        """Get all photos in an album"""
        photos = []
        page = 1
        per_page = 100
        
        while True:
            result = self.api_call(
                'flickr.photosets.getPhotos',
                photoset_id=album_id,
                user_id=self.user_id,
                extras='description,date_upload,date_taken,tags,views,url_t,url_o',
                page=page,
                per_page=per_page
            )
            
            if result['stat'] != 'ok':
                break
            
            photos.extend(result['photoset']['photo'])
            
            if page >= result['photoset']['pages']:
                break
            
            page += 1
        
        return photos
    
    def get_photo_info(self, photo_id):
        """Get detailed photo information"""
        result = self.api_call('flickr.photos.getInfo', photo_id=photo_id)
        return result['photo'] if result['stat'] == 'ok' else None
    
    def get_photo_comments(self, photo_id):
        """Get comments for a photo"""
        try:
            result = self.api_call('flickr.photos.comments.getList', photo_id=photo_id)
            if result['stat'] == 'ok' and 'comments' in result:
                return result['comments'].get('comment', [])
        except:
            pass
        return []
    
    def download_thumbnail(self, photo_id, url):
        """Download thumbnail image"""
        if not url:
            return None
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            parsed_url = urlparse(url)
            ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            
            filename = f"{photo_id}{ext}"
            filepath = self.output_dir / "thumbnails" / filename
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return str(filepath.relative_to(self.output_dir))
        except Exception as e:
            print(f"Error downloading thumbnail for {photo_id}: {e}")
            return None
    
    def save_album_metadata(self, album_id, title, description, photo_count):
        """Save album metadata to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO albums 
            (id, title, description, photo_count, created_date, updated_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (album_id, title, description, photo_count, 
              datetime.now().isoformat(), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def save_photo_metadata(self, photo_data, album_id, thumbnail_path):
        """Save photo metadata to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert tags to comma-separated string safely
        tags = ''
        if 'tags' in photo_data:
            tags_data = photo_data['tags']
            if isinstance(tags_data, dict):
                tags = tags_data.get('_content', '')
            elif isinstance(tags_data, list):
                tags = ', '.join(str(tag) for tag in tags_data)
            else:
                tags = str(tags_data)
        
        # Extract description safely
        description = ''
        if 'description' in photo_data:
            if isinstance(photo_data['description'], dict):
                description = photo_data['description'].get('_content', '')
            else:
                description = str(photo_data['description'])
        
        # Extract title safely
        title = ''
        if 'title' in photo_data:
            if isinstance(photo_data['title'], dict):
                title = photo_data['title'].get('_content', '')
            else:
                title = str(photo_data['title'])
        
        # Ensure all values are strings or numbers
        photo_id = str(photo_data['id'])
        album_id = str(album_id)
        filename = f"{photo_data['id']}.jpg"
        thumbnail_path = str(thumbnail_path) if thumbnail_path else ''
        date_taken = str(photo_data.get('datetaken', ''))
        date_uploaded = str(photo_data.get('dateupload', ''))
        views = int(photo_data.get('views', 0)) if photo_data.get('views') else 0
        url_original = str(photo_data.get('url_o', ''))
        url_thumbnail = str(photo_data.get('url_t', ''))
        
        cursor.execute("""
            INSERT OR REPLACE INTO photos 
            (id, album_id, title, description, filename, thumbnail_path, 
             date_taken, date_uploaded, views, tags, url_original, url_thumbnail)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            photo_id,
            album_id,
            title,
            description,
            filename,
            thumbnail_path,
            date_taken,
            date_uploaded,
            views,
            tags,
            url_original,
            url_thumbnail
        ))
        
        conn.commit()
        conn.close()
    
    def save_comments(self, photo_id, comments):
        """Save photo comments to database"""
        if not comments:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for comment in comments:
            cursor.execute("""
                INSERT OR REPLACE INTO comments 
                (id, photo_id, author, comment, date_created)
                VALUES (?, ?, ?, ?, ?)
            """, (
                comment['id'],
                photo_id,
                comment['authorname'],
                comment['_content'],
                comment['datecreate']
            ))
        
        conn.commit()
        conn.close()
    
    def download_album(self, album_id, album_title):
        """Download all photos and metadata for an album"""
        print(f"Downloading album: {album_title}")
        
        photos = self.get_album_photos(album_id)
        print(f"Found {len(photos)} photos in album")
        
        self.save_album_metadata(album_id, album_title, "", len(photos))
        
        for i, photo in enumerate(photos, 1):
            print(f"Processing photo {i}/{len(photos)}: {photo.get('title', 'Untitled')}")
            
            photo_info = self.get_photo_info(photo['id'])
            if photo_info:
                photo.update(photo_info)
            
            thumbnail_url = photo.get('url_t')
            thumbnail_path = self.download_thumbnail(photo['id'], thumbnail_url)
            
            comments = self.get_photo_comments(photo['id'])
            
            self.save_photo_metadata(photo, album_id, thumbnail_path)
            self.save_comments(photo['id'], comments)
        
        print(f"Album '{album_title}' downloaded successfully")
    
    def download_all_albums(self):
        """Download all albums for the user"""
        albums = self.get_user_albums()
        print(f"Found {len(albums)} albums")
        
        for album in albums:
            try:
                self.download_album(album['id'], album['title']['_content'])
            except Exception as e:
                print(f"Error downloading album {album['title']['_content']}: {e}")
        
        print("All albums downloaded!")
        print(f"Data saved to: {self.output_dir}")
        print(f"Database: {self.db_path}")

def main():
    print("=== Flickr Album Downloader with OAuth ===")
    
    # You need to provide both API key and secret
    API_KEY = input("Enter your Flickr API Key: ").strip()
    API_SECRET = input("Enter your Flickr API Secret: ").strip()
    USER_ID = '138560374@N06'  # Your client's user ID
    
    downloader = FlickrDownloaderOAuth(API_KEY, API_SECRET, USER_ID)
    
    # Try to load existing token, otherwise authenticate
    if not downloader.load_token():
        downloader.authenticate()
    
    # Test authentication by making a simple API call
    try:
        test_result = downloader.api_call('flickr.test.login')
        if test_result['stat'] == 'ok':
            print(f"✅ Authenticated as: {test_result['user']['username']['_content']}")
        else:
            print("❌ Authentication failed")
            return
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        print("🔄 Re-authenticating...")
        downloader.authenticate()
    
    # Download all albums
    downloader.download_all_albums()

if __name__ == "__main__":
    main()
