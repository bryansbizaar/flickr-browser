#!/usr/bin/env python3
"""
Flickr Local Browser - Simple Launcher
A web-based launcher that's easier to deploy
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

app = Flask(__name__)

class FlickrLauncher:
    def __init__(self):
        self.config_file = Path.home() / ".flickr_browser_config.json"
        self.config = self.load_config()
        self.download_status = {"running": False, "message": "Ready"}
        self.browser_running = False
    
    def load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_config(self, config):
        with open(self.config_file, 'w') as f:
            json.dump(config, f)

launcher = FlickrLauncher()

# HTML Template for the launcher
LAUNCHER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Flickr Local Browser Launcher</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background: #fafafa;
        }
        .section h3 {
            margin-top: 0;
            color: #333;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            margin-bottom: 15px;
            font-size: 16px;
        }
        input[type="text"]:focus, input[type="password"]:focus {
            border-color: #4CAF50;
            outline: none;
        }
        button {
            background: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
            margin-bottom: 10px;
        }
        button:hover {
            background: #45a049;
        }
        button:disabled {
            background: #cccccc;
            cursor: not-allowed;
        }
        .browse-btn {
            background: #2196F3;
        }
        .browse-btn:hover {
            background: #1976D2;
        }
        .help-btn {
            background: #ff9800;
        }
        .help-btn:hover {
            background: #f57c00;
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
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .status.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        .help-box {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px;
            border-radius: 5px;
            margin-top: 15px;
        }
        .step {
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📸 Flickr Local Browser</h1>
        <p class="subtitle">Download and browse your Flickr photos locally</p>
        
        <div class="section">
            <h3>Step 1: Enter Your Flickr API Credentials</h3>
            <form id="credentialsForm">
                <label for="api_key">API Key:</label>
                <input type="text" id="api_key" name="api_key" value="{{ config.get('api_key', '') }}" required>
                
                <label for="api_secret">API Secret:</label>
                <input type="password" id="api_secret" name="api_secret" value="{{ config.get('api_secret', '') }}" required>
                
                <label for="user_id">Flickr User ID:</label>
                <input type="text" id="user_id" name="user_id" value="{{ config.get('user_id', '') }}" required>
                
                <button type="button" onclick="saveCredentials()">💾 Save Credentials</button>
                <button type="button" onclick="showHelp()" class="help-btn">❓ How do I get these?</button>
            </form>
            
            <div id="help" class="help-box" style="display: none;">
                <h4>How to get your Flickr API credentials:</h4>
                <div class="step">1. Go to <a href="https://www.flickr.com/services/api/" target="_blank">https://www.flickr.com/services/api/</a></div>
                <div class="step">2. Click "API Keys" in the top navigation</div>
                <div class="step">3. Sign in to your Flickr account</div>
                <div class="step">4. Create a new app or find your existing app</div>
                <div class="step">5. Copy the API Key and Secret</div>
                <div class="step">6. For User ID, look at your Flickr profile URL or use <a href="https://idgettr.com/" target="_blank">idgettr.com</a></div>
            </div>
        </div>
        
        <div class="section">
            <h3>Step 2: Download Your Photos</h3>
            <p>This will download all your Flickr albums and photos with metadata.</p>
            <button onclick="startDownload()" id="downloadBtn">📥 Download All Photos</button>
            <button onclick="startUpdate()" id="updateBtn" class="browse-btn">🔄 Update (New Photos Only)</button>
            <div id="downloadStatus"></div>
        </div>
        
        <div class="section">
            <h3>Step 3: Browse Your Photos</h3>
            <p>Open the local photo browser to view your downloaded collection.</p>
            <button onclick="openBrowser()" class="browse-btn">🌐 Open Photo Browser</button>
        </div>
        
        <div id="generalStatus"></div>
    </div>

    <script>
        function showHelp() {
            const help = document.getElementById('help');
            help.style.display = help.style.display === 'none' ? 'block' : 'none';
        }
        
        function saveCredentials() {
            const formData = new FormData(document.getElementById('credentialsForm'));
            
            fetch('/save_credentials', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                showStatus('generalStatus', data.message, data.success ? 'success' : 'error');
            });
        }
        
        function startUpdate() {
            const updateBtn = document.getElementById('updateBtn');
            updateBtn.disabled = true;
            updateBtn.textContent = '⏳ Updating...';
            
            const formData = new FormData(document.getElementById('credentialsForm'));
            
            fetch('/start_update', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                showStatus('downloadStatus', data.message, data.success ? 'success' : 'error');
                if (data.success) {
                    checkDownloadStatus();
                } else {
                    updateBtn.disabled = false;
                    updateBtn.textContent = '🔄 Update (New Photos Only)';
                }
            });
        }
        
        function startDownload() {
            const downloadBtn = document.getElementById('downloadBtn');
            downloadBtn.disabled = true;
            downloadBtn.textContent = '⏳ Downloading...';
            
            const formData = new FormData(document.getElementById('credentialsForm'));
            
            fetch('/start_download', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                showStatus('downloadStatus', data.message, data.success ? 'success' : 'error');
                if (data.success) {
                    checkDownloadStatus();
                } else {
                    downloadBtn.disabled = false;
                    downloadBtn.textContent = '📥 Download All Photos';
                }
            });
        }
        
        function checkDownloadStatus() {
            fetch('/download_status')
            .then(response => response.json())
            .then(data => {
                showStatus('downloadStatus', data.message, 'info');
                
                if (data.running) {
                    setTimeout(checkDownloadStatus, 2000);
                } else {
                    const downloadBtn = document.getElementById('downloadBtn');
                    downloadBtn.disabled = false;
                    downloadBtn.textContent = '📥 Download All Photos';
                    
                    if (data.message.includes('complete')) {
                        showStatus('downloadStatus', data.message, 'success');
                    }
                }
            });
        }
        
        function openBrowser() {
            fetch('/open_browser', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                showStatus('generalStatus', data.message, data.success ? 'success' : 'info');
                if (data.success) {
                    setTimeout(() => {
                        window.open('http://127.0.0.1:8081', '_blank');
                    }, 2000);
                }
            });
        }
        
        function showStatus(elementId, message, type) {
            const statusDiv = document.getElementById(elementId);
            statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(LAUNCHER_HTML, config=launcher.config)

@app.route('/save_credentials', methods=['POST'])
def save_credentials():
    try:
        config = {
            'api_key': request.form.get('api_key'),
            'api_secret': request.form.get('api_secret'),
            'user_id': request.form.get('user_id')
        }
        launcher.save_config(config)
        launcher.config = config
        return jsonify({"success": True, "message": "✅ Credentials saved successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"❌ Error saving credentials: {e}"})

@app.route('/start_update', methods=['POST'])
def start_update():
    if launcher.download_status["running"]:
        return jsonify({"success": False, "message": "Download already in progress"})
    
    api_key = request.form.get('api_key')
    api_secret = request.form.get('api_secret')
    user_id = request.form.get('user_id')
    
    if not all([api_key, api_secret, user_id]):
        return jsonify({"success": False, "message": "❌ Please fill in all credentials"})
    
    # Save credentials
    config = {'api_key': api_key, 'api_secret': api_secret, 'user_id': user_id}
    launcher.save_config(config)
    launcher.config = config
    
    # Start incremental update in background
    def run_update():
        try:
            launcher.download_status = {"running": True, "message": "🔄 Checking for new photos..."}
            
            # Run true incremental updater
            print(f"DEBUG: Running incremental updater from {os.path.join(os.path.dirname(__file__))}")
            result = subprocess.run([sys.executable, "incremental_updater_true.py"], 
                                  capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__)))
            
            print(f"DEBUG: Return code: {result.returncode}")
            print(f"DEBUG: Stdout: {result.stdout}")
            print(f"DEBUG: Stderr: {result.stderr}")
            
            if result.returncode == 0:
                if "No new photos found" in result.stdout:
                    launcher.download_status = {"running": False, "message": "✅ You're up to date! No new photos found."}
                elif "completed" in result.stdout:
                    launcher.download_status = {"running": False, "message": "✅ Update completed! New photos added."}
                elif "OAuth authentication required" in result.stdout:
                    launcher.download_status = {"running": False, "message": "🔐 OAuth authentication required - redirecting to Flickr..."}
                else:
                    launcher.download_status = {"running": False, "message": "✅ Update process completed"}
            elif result.returncode == 2:  # Auth needed
                launcher.download_status = {"running": False, "message": "🔐 OAuth authentication required - please complete Flickr authorization"}
            else:
                error_msg = result.stderr if result.stderr else result.stdout if result.stdout else "Unknown error"
                launcher.download_status = {"running": False, "message": f"❌ Update failed: {error_msg}"}
                
        except Exception as e:
            launcher.download_status = {"running": False, "message": f"❌ Error: {e}"}
    
    thread = threading.Thread(target=run_update)
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True, "message": "🔄 Update started!"})

@app.route('/start_download', methods=['POST'])
def start_download():
    if launcher.download_status["running"]:
        return jsonify({"success": False, "message": "Download already in progress"})
    
    api_key = request.form.get('api_key')
    api_secret = request.form.get('api_secret')
    user_id = request.form.get('user_id')
    
    if not all([api_key, api_secret, user_id]):
        return jsonify({"success": False, "message": "❌ Please fill in all credentials"})
    
    # Save credentials
    config = {'api_key': api_key, 'api_secret': api_secret, 'user_id': user_id}
    launcher.save_config(config)
    launcher.config = config
    
    # Start download in background
    def run_download():
        try:
            launcher.download_status = {"running": True, "message": "🔐 Authenticating with Flickr..."}
            
            # Create download script
            script_content = f'''
import sys
import os
sys.path.append(os.path.dirname(__file__))

try:
    from oauth_downloader import FlickrDownloaderOAuth
    
    API_KEY = "{api_key}"
    API_SECRET = "{api_secret}"
    USER_ID = "{user_id}"
    
    downloader = FlickrDownloaderOAuth(API_KEY, API_SECRET, USER_ID)
    
    if not downloader.load_token():
        print("NEED_AUTH")
    else:
        print("DOWNLOADING")
        downloader.download_all_albums()
        print("COMPLETE")
        
except Exception as e:
    print(f"ERROR: {{e}}")
'''
            
            # Write and run script
            temp_script = Path("temp_download.py")
            with open(temp_script, 'w') as f:
                f.write(script_content)
            
            result = subprocess.run([sys.executable, str(temp_script)], 
                                  capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            if "NEED_AUTH" in result.stdout:
                launcher.download_status = {"running": False, "message": "🔐 Authentication required - please run OAuth setup first"}
            elif "COMPLETE" in result.stdout:
                launcher.download_status = {"running": False, "message": "✅ Download completed successfully!"}
            elif "ERROR" in result.stdout:
                launcher.download_status = {"running": False, "message": f"❌ Error: {result.stdout}"}
            else:
                launcher.download_status = {"running": False, "message": "✅ Download process completed"}
            
            # Clean up
            if temp_script.exists():
                temp_script.unlink()
                
        except Exception as e:
            launcher.download_status = {"running": False, "message": f"❌ Error: {e}"}
    
    thread = threading.Thread(target=run_download)
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True, "message": "🚀 Download started!"})

@app.route('/download_status')
def download_status():
    return jsonify(launcher.download_status)

@app.route('/open_browser', methods=['POST'])
def open_browser():
    try:
        if not launcher.browser_running:
            # Start the photo browser server
            def start_browser_server():
                launcher.browser_running = True
                try:
                    from server import app as browser_app
                    browser_app.run(host='127.0.0.1', port=8081, debug=False, use_reloader=False)
                except Exception as e:
                    print(f"Browser server error: {e}")
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
    print("=== Flickr Local Browser Launcher ===")
    print("Opening launcher at: http://127.0.0.1:9000")
    
    # Open the launcher in browser
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:9000")).start()
    
    app.run(host='127.0.0.1', port=9000, debug=False)
