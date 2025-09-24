#!/usr/bin/env python3
"""
Enhanced Flask server for the Flickr Local Browser
Adds photo detail modal while keeping album grid unchanged
"""

from flask import Flask, jsonify, request, send_from_directory, render_template_string
import sqlite3
import os
from pathlib import Path

app = Flask(__name__)

class EnhancedFlickrServer:
    def __init__(self, data_dir="data"):
        if not os.path.isabs(data_dir):
            data_dir = os.path.abspath(data_dir)
        
        self.data_dir = Path(data_dir)
        self.db_path = self.data_dir / "flickr_metadata.db"
        self.thumbnails_dir = self.data_dir / "thumbnails"
        
        print(f"Looking for database at: {self.db_path}")
        print(f"Looking for thumbnails at: {self.thumbnails_dir}")
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}")
        
        if not self.thumbnails_dir.exists():
            print(f"Warning: Thumbnails directory not found at {self.thumbnails_dir}")
    
    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_albums(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Get albums with actual photo counts from junction table
        cursor.execute("""
            SELECT 
                a.id,
                a.title,
                a.description,
                a.photo_count as stored_photo_count,
                COALESCE(pa.photo_count, 0) as photo_count
            FROM albums a
            LEFT JOIN (
                SELECT album_id, COUNT(*) as photo_count
                FROM photo_albums
                GROUP BY album_id
            ) pa ON a.id = pa.album_id
            ORDER BY a.title
        """)
        
        albums = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return albums
    
    def get_photos(self, album_id=None, search_term=None, limit=100, offset=0):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        if album_id:
            # Use junction table to get photos for specific album
            query = """
                SELECT p.* FROM photos p
                INNER JOIN photo_albums pa ON p.id = pa.photo_id
                WHERE pa.album_id = ?
            """
            params = [album_id]
            
            # Add search term filter for album-specific queries
            if search_term:
                query += " AND (p.title LIKE ? OR p.description LIKE ? OR p.tags LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern])
        else:
            # General query for all photos
            query = "SELECT * FROM photos WHERE 1=1"
            params = []
            
            # Add search term filter for general queries
            if search_term:
                query += " AND (title LIKE ? OR description LIKE ? OR tags LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern])
        
        query += " ORDER BY date_taken DESC"
        
        # Only add LIMIT and OFFSET if limit is specified
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        cursor.execute(query, params)
        photos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return photos
    
    def get_photo_details(self, photo_id):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Get photo details
        cursor.execute("SELECT * FROM photos WHERE id = ?", (photo_id,))
        photo = cursor.fetchone()
        
        if not photo:
            conn.close()
            return None
        
        photo = dict(photo)
        
        # Get all albums this photo is in
        cursor.execute("""
            SELECT DISTINCT a.id, a.title 
            FROM albums a 
            JOIN photo_albums pa ON a.id = pa.album_id
            WHERE pa.photo_id = ?
            ORDER BY a.title
        """, (photo_id,))
        
        photo_albums = [dict(row) for row in cursor.fetchall()]
        photo['albums'] = photo_albums
        
        # Get comments
        cursor.execute("SELECT * FROM comments WHERE photo_id = ? ORDER BY comment_date", (photo_id,))
        comments = [dict(row) for row in cursor.fetchall()]
        photo['comments'] = comments
        
        conn.close()
        return photo

# Initialize server
server = EnhancedFlickrServer()

@app.route('/')
def index():
    """Serve the HTML page with photo detail modal"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flickr Local Browser</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            color: #333;
        }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        
        header {
            background: #0063dc;
            color: white;
            padding: 20px 0;
            margin-bottom: 30px;
            border-radius: 8px;
        }
        
        .header-content { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
        h1 { font-size: 2.5em; margin-bottom: 10px; }
        
        .search-section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .search-controls {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .search-input {
            flex: 1;
            min-width: 200px;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 16px;
        }
        
        .search-input:focus { outline: none; border-color: #0063dc; }
        
        .filter-select {
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 16px;
            min-width: 150px;
        }
        
        .search-btn {
            background: #0063dc;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .search-btn:hover { background: #0056c4; }
        
        .albums-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .album-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .album-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
        
        .album-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #0063dc;
        }
        
        .album-count { color: #666; font-size: 0.9em; }
        
        .photos-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
        }
        
        .photo-card {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .photo-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
        
        .photo-thumbnail {
            width: 100%;
            height: 200px;
            object-fit: cover;
            cursor: pointer;
        }
        
        .photo-info { padding: 15px; }
        
        .photo-title {
            font-weight: bold;
            margin-bottom: 8px;
            color: #333;
        }
        
        .photo-description {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .photo-meta {
            font-size: 0.8em;
            color: #999;
            border-top: 1px solid #eee;
            padding-top: 10px;
        }
        
        .back-btn {
            background: #666;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            margin-bottom: 20px;
            font-size: 16px;
        }
        
        .back-btn:hover { background: #555; }
        
        .results-count {
            margin-bottom: 20px;
            font-size: 1.1em;
            color: #666;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        
        /* Photo Detail Modal */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.8);
        }
        
        .modal-content {
            background-color: white;
            margin: 3% auto;
            padding: 0;
            border-radius: 8px;
            width: 90%;
            max-width: 600px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .modal-header {
            padding: 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .modal-title {
            font-size: 1.4em;
            font-weight: bold;
            color: #333;
            margin: 0;
        }
        
        .close {
            color: #aaa;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            line-height: 1;
        }
        
        .close:hover { color: #000; }
        
        .modal-body {
            padding: 20px;
        }
        
        .detail-section {
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .detail-section:last-child {
            border-bottom: none;
            margin-bottom: 0;
        }
        
        .detail-label {
            font-weight: bold;
            color: #0063dc;
            margin-bottom: 8px;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .detail-content {
            color: #333;
            line-height: 1.5;
        }
        
        .tag {
            display: inline-block;
            background: #e3f2fd;
            color: #0063dc;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            margin-right: 6px;
            margin-bottom: 6px;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .tag:hover { 
            background: #bbdefb;
            text-decoration: underline;
        }
        
        .album-list {
            list-style: none;
        }
        
        .album-list li {
            padding: 8px 0;
            border-bottom: 1px solid #f5f5f5;
            color: #0063dc;
            cursor: pointer;
        }
        
        .album-list li:hover {
            text-decoration: underline;
        }
        
        .album-list li:last-child {
            border-bottom: none;
        }
        
        .no-data {
            color: #999;
            font-style: italic;
        }
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <h1>📸 Flickr Local Browser</h1>
            <p>Browse your downloaded Flickr albums and photos locally</p>
        </div>
    </header>

    <div class="container">
        <div class="search-section">
            <div class="search-controls">
                <input type="text" class="search-input" id="searchInput" placeholder="Search photos by title, description, or tags...">
                <select class="filter-select" id="albumFilter">
                    <option value="">All Albums</option>
                </select>
                <button class="search-btn" onclick="searchPhotos()">Search</button>
                <button class="search-btn" onclick="clearSearch()">Clear</button>
            </div>
        </div>

        <div id="albumsView">
            <div class="albums-grid" id="albumsGrid">
                <!-- Albums will be loaded here -->
            </div>
        </div>

        <div id="photosView" style="display: none;">
            <button class="back-btn" onclick="showAlbums()">← Back to Albums</button>
            <div class="results-count" id="resultsCount"></div>
            <div class="photos-grid" id="photosGrid">
                <!-- Photos will be loaded here -->
            </div>
        </div>
    </div>

    <!-- Photo Detail Modal -->
    <div id="photoModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title" id="modalTitle">Photo Details</h2>
                <span class="close" onclick="closeModal()">&times;</span>
            </div>
            <div class="modal-body" id="modalBody">
                <!-- Photo details will be loaded here -->
            </div>
        </div>
    </div>

    <script>
        let currentAlbumId = null;
        let albums = [];

        async function loadAlbums() {
            try {
                const response = await fetch('/api/albums');
                albums = await response.json();
                
                const albumsGrid = document.getElementById('albumsGrid');
                const albumFilter = document.getElementById('albumFilter');
                
                albumsGrid.innerHTML = '';
                albumFilter.innerHTML = '<option value="">All Albums</option>';
                
                albums.forEach(album => {
                    const albumCard = document.createElement('div');
                    albumCard.className = 'album-card';
                    albumCard.onclick = () => showAlbumPhotos(album.id);
                    albumCard.innerHTML = `
                        <div class="album-title">${album.title}</div>
                        <div class="album-count">${album.photo_count} photos</div>
                    `;
                    albumsGrid.appendChild(albumCard);
                    
                    const option = document.createElement('option');
                    option.value = album.id;
                    option.textContent = album.title;
                    albumFilter.appendChild(option);
                });
            } catch (error) {
                console.error('Error loading albums:', error);
                document.getElementById('albumsGrid').innerHTML = '<div class="error">Error loading albums</div>';
            }
        }

        async function showAlbumPhotos(albumId) {
            currentAlbumId = albumId;
            const album = albums.find(a => a.id === albumId);
            
            try {
                const response = await fetch(`/api/photos?album_id=${albumId}`);
                const photos = await response.json();
                
                displayPhotos(photos);
                document.getElementById('albumsView').style.display = 'none';
                document.getElementById('photosView').style.display = 'block';
                document.getElementById('resultsCount').textContent = `${photos.length} photos in "${album.title}"`;
            } catch (error) {
                console.error('Error loading photos:', error);
                document.getElementById('photosGrid').innerHTML = '<div class="error">Error loading photos</div>';
            }
        }

        function showAlbums() {
            currentAlbumId = null;
            document.getElementById('albumsView').style.display = 'block';
            document.getElementById('photosView').style.display = 'none';
            document.getElementById('searchInput').value = '';
            document.getElementById('albumFilter').value = '';
        }

        function displayPhotos(photos) {
            const photosGrid = document.getElementById('photosGrid');
            photosGrid.innerHTML = '';
            
            photos.forEach(photo => {
                const photoCard = document.createElement('div');
                photoCard.className = 'photo-card';
                
                const thumbnailUrl = photo.thumbnail_path ? `/thumbnails/${photo.thumbnail_path.split('/').pop()}` : '/static/placeholder.jpg';
                const dateTaken = photo.date_taken ? new Date(photo.date_taken).toLocaleDateString() : 'Unknown';
                
                photoCard.innerHTML = `
                    <img src="${thumbnailUrl}" alt="${photo.title || 'Untitled'}" class="photo-thumbnail" onclick="showPhotoDetails('${photo.id}')">
                    <div class="photo-info">
                        <div class="photo-title">${photo.title || 'Untitled'}</div>
                        <div class="photo-description">${photo.description || ''}</div>
                        <div class="photo-meta">
                            📅 ${dateTaken}
                        </div>
                    </div>
                `;
                photosGrid.appendChild(photoCard);
            });
        }

        async function showPhotoDetails(photoId) {
            console.log('Clicked photo ID:', photoId); // Debug log
            try {
                const response = await fetch(`/api/photos/${photoId}`);
                console.log('Response status:', response.status); // Debug log
                const photo = await response.json();
                console.log('Photo data:', photo); // Debug log
                
                const modal = document.getElementById('photoModal');
                const modalTitle = document.getElementById('modalTitle');
                const modalBody = document.getElementById('modalBody');
                
                modalTitle.textContent = photo.title || 'Untitled';
                
                // Format date taken
                const dateTaken = photo.date_taken ? new Date(photo.date_taken).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                }) : 'Unknown';
                
                // Process tags
                let tagsHtml = '<span class="no-data">No tags</span>';
                if (photo.tags && photo.tags.trim()) {
                    // Handle both comma-separated and space-separated tags
                let tagList;
                if (photo.tags.includes(',')) {
                    tagList = photo.tags.split(',').map(tag => tag.trim()).filter(tag => tag);
                } else {
                    tagList = photo.tags.split(' ').map(tag => tag.trim()).filter(tag => tag);
                }
                    if (tagList.length > 0) {
                        tagsHtml = tagList.map(tag => 
                            `<span class="tag" onclick="searchByTag('${tag}'); closeModal();">${tag}</span>`
                        ).join('');
                    }
                }
                
                // Process albums
                let albumsHtml = '<span class="no-data">Not in any albums</span>';
                if (photo.albums && photo.albums.length > 0) {
                    albumsHtml = '<ul class="album-list">' + 
                        photo.albums.map(album => 
                            `<li onclick="showAlbumPhotos('${album.id}'); closeModal();">${album.title}</li>`
                        ).join('') + 
                        '</ul>';
                }
                
                modalBody.innerHTML = `
                    <div class="detail-section">
                        <div class="detail-label">Title</div>
                        <div class="detail-content">${photo.title || '<span class="no-data">No title</span>'}</div>
                    </div>
                    
                    <div class="detail-section">
                        <div class="detail-label">Description</div>
                        <div class="detail-content">${photo.description || '<span class="no-data">No description</span>'}</div>
                    </div>
                    
                    <div class="detail-section">
                        <div class="detail-label">Date Taken</div>
                        <div class="detail-content">${dateTaken}</div>
                    </div>
                    
                    <div class="detail-section">
                        <div class="detail-label">Albums (${photo.albums ? photo.albums.length : 0})</div>
                        <div class="detail-content">${albumsHtml}</div>
                    </div>
                    
                    <div class="detail-section">
                        <div class="detail-label">Tags</div>
                        <div class="detail-content">${tagsHtml}</div>
                    </div>
                `;
                
                modal.style.display = 'block';
            } catch (error) {
                console.error('Error loading photo details:', error);
                alert('Error loading photo details');
            }
        }

        function closeModal() {
            document.getElementById('photoModal').style.display = 'none';
        }

        async function searchPhotos() {
            const searchTerm = document.getElementById('searchInput').value;
            const selectedAlbum = document.getElementById('albumFilter').value;
            
            try {
                let url = '/api/photos?';
                const params = new URLSearchParams();
                
                if (searchTerm) params.append('search', searchTerm);
                if (selectedAlbum) params.append('album_id', selectedAlbum);
                
                const response = await fetch(url + params.toString());
                const photos = await response.json();
                
                displayPhotos(photos);
                document.getElementById('albumsView').style.display = 'none';
                document.getElementById('photosView').style.display = 'block';
                
                let resultText = `${photos.length} photos found`;
                if (searchTerm) resultText += ` for "${searchTerm}"`;
                if (selectedAlbum) {
                    const album = albums.find(a => a.id === selectedAlbum);
                    if (album) resultText += ` in "${album.title}"`;
                }
                
                document.getElementById('resultsCount').textContent = resultText;
            } catch (error) {
                console.error('Error searching photos:', error);
                document.getElementById('photosGrid').innerHTML = '<div class="error">Error searching photos</div>';
            }
        }

        function searchByTag(tag) {
            document.getElementById('searchInput').value = tag;
            searchPhotos();
        }

        function clearSearch() {
            document.getElementById('searchInput').value = '';
            document.getElementById('albumFilter').value = '';
            if (currentAlbumId) {
                showAlbumPhotos(currentAlbumId);
            } else {
                showAlbums();
            }
        }

        // Event listeners
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchPhotos();
            }
        });

        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('photoModal');
            if (event.target === modal) {
                closeModal();
            }
        };

        // Initialize
        loadAlbums();
    </script>
</body>
</html>
    """
    return html_content

@app.route('/api/albums')
def get_albums():
    try:
        albums = server.get_albums()
        return jsonify(albums)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/photos')
def get_photos():
    try:
        album_id = request.args.get('album_id')
        search_term = request.args.get('search')
        
        # If viewing a specific album, NEVER limit results
        # Only use limits for general searches without album filter
        if album_id:
            limit = None  # Show ALL photos in any album, regardless of size
            offset = 0
        else:
            # Only limit when doing general searches across all photos
            limit = int(request.args.get('limit', 1000))  # Higher default for searches
            offset = int(request.args.get('offset', 0))
        
        photos = server.get_photos(album_id, search_term, limit, offset)
        return jsonify(photos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/photos/<photo_id>')
def get_photo_details(photo_id):
    try:
        photo = server.get_photo_details(photo_id)
        if photo:
            return jsonify(photo)
        else:
            return jsonify({'error': 'Photo not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/thumbnails/<filename>')
def serve_thumbnail(filename):
    """Serve thumbnail images"""
    try:
        print(f"Serving thumbnail: {filename}")
        print(f"From directory: {server.thumbnails_dir}")
        
        # Check if file exists
        file_path = server.thumbnails_dir / filename
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return "File not found", 404
        
        return send_from_directory(server.thumbnails_dir, filename)
    except Exception as e:
        print(f"Error serving thumbnail {filename}: {e}")
        return "Error serving file", 500

if __name__ == "__main__":
    print("Starting Flickr Local Browser with Photo Details...")
    print("Open your browser and go to: http://localhost:8080")
    app.run(host='127.0.0.1', port=8080, debug=True)
