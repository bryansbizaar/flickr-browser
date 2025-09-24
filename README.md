# 📸 Flickr Local Browser

A complete desktop application for downloading and browsing Flickr photo collections locally, with advanced search and album management capabilities.

> **Note**: This is a portfolio demonstration version of a custom application originally built for a private client. Personal data has been replaced with realistic demo content to showcase the technical implementation and user experience.

## 🎯 Quick Demo

**Want to see it in action immediately?**

```bash
git clone https://github.com/your-username/flickr-local-browser
cd flickr-local-browser
python3 setup_portfolio_demo.py
python3 PORTFOLIO_LAUNCHER.py
```

The demo will automatically:

- ✅ Create 10 realistic photo albums
- ✅ Generate 400+ demo photos with rich metadata
- ✅ Set up a working photo browser interface
- ✅ Launch directly in your browser

## 🚀 Complete Setup Guide

### First Time Setup (Portfolio Demo)

1. **Clone & Navigate**

   ```bash
   git clone https://github.com/your-username/flickr-local-browser
   cd flickr-local-browser
   ```

2. **Setup Demo Environment**

   ```bash
   python3 setup_portfolio_demo.py
   ```

   This creates the virtual environment, installs dependencies, and generates demo data.

3. **Launch Portfolio Demo**
   ```bash
   python3 PORTFOLIO_LAUNCHER.py
   ```
   Browser opens automatically with the portfolio interface!

### For Real Flickr Data (Production Use)

1. **Setup Environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Get Flickr API Credentials**

   - Go to [Flickr App Garden](https://www.flickr.com/services/apps/create/)
   - Create a new app to get your API key and secret
   - Find your Flickr User ID from your profile URL

3. **Launch Application**
   ```bash
   python3 START_FLICKR_BROWSER.py
   ```
   Enter your API credentials in the web interface that opens.

## 🛑 How to Stop

- Press **Ctrl+C** in Terminal
- Type `exit` or close Terminal window

## 🔄 Restart Instructions

**Portfolio Demo:**

```bash
cd flickr-local-browser
python3 PORTFOLIO_LAUNCHER.py
```

**Production Version:**

```bash
cd flickr-local-browser
source venv/bin/activate
python3 START_FLICKR_BROWSER.py
```

## ⚠️ Important Notes

- Keep Terminal window open while using the app
- Don't close Terminal until you're done browsing photos
- If Terminal closes accidentally, just restart using the steps above
- Portfolio demo works offline - no API keys needed!

## 🎮 Demo Features

The portfolio demo includes:

- **10 Realistic Albums**: Summer Vacation, Family Gathering, Nature Photography, etc.
- **400+ Demo Photos**: Real images with rich metadata and descriptions
- **Advanced Search**: Search by title, description, tags, or album
- **Photo Details**: Click any photo to see detailed information, tags, and comments
- **Album Navigation**: Browse by album or search across all photos
- **Responsive Design**: Works on desktop and tablet browsers

## 🔧 Technical Highlights

- **Database Architecture**: SQLite with proper many-to-many relationships
- **Backend**: Python Flask with RESTful API endpoints
- **Frontend**: Responsive HTML/CSS/JavaScript
- **Photo Management**: Automatic thumbnail generation and metadata extraction
- **Search Engine**: Full-text search across titles, descriptions, and tags
- **Schema Migration**: Solved complex database relationship challenges
- **Incremental Updates**: Sync only new photos since last download
- **API Rate Limiting**: Respectful Flickr API usage with proper throttling
- **Error Handling**: Graceful fallbacks and user-friendly error messages

## 📁 Project Structure

```
flickr-local-browser/
├── PORTFOLIO_LAUNCHER.py      # Demo launcher (portfolio version)
├── START_FLICKR_BROWSER.py    # Production launcher
├── setup_portfolio_demo.py    # Demo setup script
├── requirements.txt           # Python dependencies
├── src/                       # Application source code
│   ├── server.py             # Photo browser web server
│   ├── launcher.py           # Production setup interface
│   └── oauth_downloader.py   # Flickr API integration
├── data/                     # Photo storage (auto-created)
│   ├── thumbnails/          # Photo thumbnail images
│   └── flickr_metadata.db   # SQLite database
└── venv/                     # Python virtual environment
```

## 🏆 Project Background

This application was **custom-developed for a private client** who needed:

- Complete offline access to their extensive Flickr photo collection
- Advanced search and organization capabilities beyond Flickr's web interface
- Privacy and control over their personal photo data
- Professional-grade photo management tools

The client project involved:

- **8,000+ real photos** with full metadata extraction
- **70+ actual photo albums** with complex many-to-many relationships
- **OAuth authentication** for accessing private family photos
- **Database schema migration** to solve photo-album association challenges
- **Incremental sync capabilities** to download only new photos
- **Automated update system** to keep local collection current with Flickr

**This demo version** replicates the full functionality using generated sample data to protect client privacy while demonstrating the complete technical implementation.

## 🎯 Key Achievements

This project demonstrates:

- **Complex Problem Solving**: Migrated database from 1:1 to many:many relationships without data loss
- **API Integration**: OAuth authentication with rate limiting and pagination handling
- **Full-Stack Development**: Complete application from database to user interface
- **User Experience Design**: Intuitive interface that matches familiar photo browsing patterns
- **Production Ready**: Error handling, logging, and deployment considerations
- **Performance Optimization**: Efficient queries and thumbnail management for large photo collections

## 🔗 Links

- **GitHub Repository**: [Source Code](https://github.com/bryansbizaar/flickr-browser)
- **Quick Setup**: See [Quick Demo](#-quick-demo) section above
- **Documentation**: [Complete Usage Guide](USAGE.txt)

---

_Built with Python Flask, SQLite database, and modern CSS Grid layouts. Designed for photographers and photo enthusiasts who want complete control over their photo collections._
