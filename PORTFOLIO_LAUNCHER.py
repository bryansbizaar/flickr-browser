#!/usr/bin/env python3
"""
Portfolio Demo Launcher for Flickr Local Browser
Automatically detects demo data and goes straight to photo browser
"""

from flask import Flask, render_template_string, request, jsonify, redirect
import subprocess
import threading
import os
import sys
import json
import webbrowser
from pathlib import Path
import time
import sqlite3

app = Flask(__name__)

def has_demo_data():
    """Check if demo data exists"""
    db_path = Path("data/flickr_metadata.db")
    if not db_path.exists():
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM albums")
        album_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM photos") 
        photo_count = cursor.fetchone()[0]
        conn.close()
        return album_count > 0 and photo_count > 0
    except:
        return False

def get_demo_stats():
    """Get demo data statistics"""
    if not has_demo_data():
        return None
    
    try:
        db_path = Path("data/flickr_metadata.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM albums")
        album_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM photos")
        photo_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comments")
        comment_count = cursor.fetchone()[0]
        
        # Get some sample album names
        cursor.execute("SELECT title FROM albums ORDER BY title LIMIT 5")
        sample_albums = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'albums': album_count,
            'photos': photo_count,
            'comments': comment_count,
            'sample_albums': sample_albums
        }
    except Exception as e:
        print(f"Error getting demo stats: {e}")
        return None

class PortfolioLauncher:
    def __init__(self):
        self.browser_running = False

launcher = PortfolioLauncher()

# HTML Template for the portfolio demo
DEMO_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Flickr Local Browser - Portfolio Demo</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5rem;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.2rem;
        }
        .demo-badge {
            background: #ff6b6b;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            display: inline-block;
            font-weight: bold;
            margin-bottom: 30px;
            font-size: 0.9rem;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 2px solid #e9ecef;
        }
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #495057;
            margin-bottom: 5px;
        }
        .stat-label {
            color: #6c757d;
            font-size: 0.9rem;
        }
        .demo-info {
            background: #e3f2fd;
            border: 1px solid #bbdefb;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .demo-info h3 {
            margin-top: 0;
            color: #1565c0;
        }
        .album-list {
            list-style: none;
            padding: 0;
            margin: 10px 0;
        }
        .album-list li {
            background: white;
            padding: 8px 15px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 4px solid #2196f3;
        }
        .btn-primary {
            background: #2196f3;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1.1rem;
            font-weight: bold;
            display: block;
            width: 100%;
            margin-bottom: 15px;
            transition: background 0.3s;
        }
        .btn-primary:hover {
            background: #1976d2;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9rem;
            text-decoration: none;
            display: inline-block;
            margin: 5px;
        }
        .btn-secondary:hover {
            background: #5a6268;
        }
        .features {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }
        .features h3 {
            margin-top: 0;
            color: #333;
        }
        .feature-list {
            list-style: none;
            padding: 0;
        }
        .feature-list li {
            padding: 5px 0;
            color: #495057;
        }
        .feature-list li::before {
            content: "✅ ";
            margin-right: 8px;
        }
        .status {
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
            font-weight: bold;
        }
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📸 Flickr Local Browser</h1>
        <div class="demo-badge">PORTFOLIO DEMO</div>
        <p class="subtitle">Interactive Photo Management & Search Application</p>
        
        {% if stats %}
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{{ stats.albums }}</div>
                <div class="stat-label">Photo Albums</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.photos }}</div>
                <div class="stat-label">Photos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.comments }}</div>
                <div class="stat-label">Comments</div>
            </div>
        </div>
        
        <div class="demo-info">
            <h3>🎮 Demo Features</h3>
            <p>This portfolio demo showcases a complete photo management application with:</p>
            <ul class="feature-list">
                <li>Album-based photo organization</li>
                <li>Advanced search by title, tags, and descriptions</li>
                <li>Many-to-many photo-album relationships</li>
                <li>Responsive web interface</li>
                <li>SQLite database with proper schema design</li>
                <li>Real-time thumbnail browsing</li>
            </ul>
            
            <h4>Sample Albums:</h4>
            <ul class="album-list">
                {% for album in stats.sample_albums %}
                <li>📁 {{ album }}</li>
                {% endfor %}
                {% if stats.albums > 5 %}
                <li style="font-style: italic; color: #666;">... and {{ stats.albums - 5 }} more albums</li>
                {% endif %}
            </ul>
        </div>
        
        <button onclick="openBrowser()" class="btn-primary">
            🌐 Launch Photo Browser Demo
        </button>
        
        <div class="features">
            <h3>🔧 Technical Highlights</h3>
            <ul class="feature-list">
                <li>Flask web application with SQLite backend</li>
                <li>Complex database schema migration (1:1 to many:many)</li>
                <li>OAuth API integration with rate limiting</li>
                <li>Automated data synchronization</li>
                <li>Error handling and graceful fallbacks</li>
                <li>Clean, maintainable Python code structure</li>
            </ul>
        </div>
        {% else %}
        <div class="demo-info">
            <h3>⚠️ Demo Data Not Found</h3>
            <p>The demo data hasn't been generated yet. To set up the portfolio demo:</p>
            <ol>
                <li>Run: <code>python3 setup_portfolio_demo.py</code></li>
                <li>Wait for photo generation to complete</li>
                <li>Restart this launcher</li>
            </ol>
        </div>
        {% endif %}
        
        <div id="status"></div>
        
        <div style="text-align: center; margin-top: 30px;">
            <a href="#" onclick="showTechnicalDetails()" class="btn-secondary">📋 Technical Details</a>
            <a href="https://github.com/your-username/flickr-local-browser" class="btn-secondary">🔗 View on GitHub</a>
        </div>
    </div>

    <script>
        function openBrowser() {
            fetch('/open_browser', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                showStatus(data.message, data.success ? 'success' : 'info');
                if (data.success) {
                    setTimeout(() => {
                        window.open('http://127.0.0.1:8081', '_blank');
                    }, 2000);
                }
            })
            .catch(error => {
                showStatus('❌ Error starting browser: ' + error, 'error');
            });
        }
        
        function showTechnicalDetails() {
            alert(`Technical Implementation Details:

🏗️ Architecture:
• Python Flask web application
• SQLite database with junction tables
• Responsive HTML/CSS frontend
• RESTful API endpoints

🗃️ Database Schema:
• Albums table (metadata)
• Photos table (image data)
• Photo_albums junction table (many-to-many)
• Comments table (user interactions)

🔧 Key Features Implemented:
• OAuth API authentication
• Incremental data synchronization
• Advanced search and filtering
• Error handling and recovery
• Rate limit compliance
• Schema migration tools`);
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '<div class="status ' + type + '">' + message + '</div>';
        }
        
        // Auto-launch browser if requested
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('autolaunch') === 'true') {
            setTimeout(() => openBrowser(), 1000);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    stats = get_demo_stats()
    return render_template_string(DEMO_HTML, stats=stats)

@app.route('/open_browser', methods=['POST'])
def open_browser():
    try:
        if not has_demo_data():
            return jsonify({"success": False, "message": "❌ Demo data not found. Please run setup_portfolio_demo.py first."})
        
        if not launcher.browser_running:
            # Start the photo browser server
            def start_browser_server():
                launcher.browser_running = True
                try:
                    # Add src directory to Python path instead of changing working directory
                    import sys
                    src_dir = os.path.join(os.path.dirname(__file__), 'src')
                    if src_dir not in sys.path:
                        sys.path.insert(0, src_dir)
                    
                    # Import and run the server
                    from server import app as browser_app
                    print(f"Starting browser server on port 8081...")
                    browser_app.run(host='127.0.0.1', port=8081, debug=False, use_reloader=False)
                except Exception as e:
                    print(f"Browser server error: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    launcher.browser_running = False
            
            thread = threading.Thread(target=start_browser_server)
            thread.daemon = True
            thread.start()
            
            return jsonify({"success": True, "message": "🌐 Starting photo browser... Opening in 2 seconds"})
        else:
            return jsonify({"success": True, "message": "🌐 Photo browser is already running"})
    except Exception as e:
        return jsonify({"success": False, "message": f"❌ Error starting browser: {e}"})

if __name__ == "__main__":
    print("=== Flickr Local Browser - Portfolio Demo ===")
    
    if has_demo_data():
        stats = get_demo_stats()
        print(f"✅ Demo data found: {stats['albums']} albums, {stats['photos']} photos")
        print("🌐 Opening portfolio demo at: http://127.0.0.1:9000")
        
        # Open the demo in browser
        threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:9000")).start()
    else:
        print("⚠️ No demo data found. Please run: python3 setup_portfolio_demo.py")
        print("🌐 Opening setup interface at: http://127.0.0.1:9000")
        threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:9000")).start()
    
    app.run(host='127.0.0.1', port=9000, debug=False)