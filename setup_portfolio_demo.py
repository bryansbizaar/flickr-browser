#!/usr/bin/env python3
"""
Setup script that handles virtual environment creation for portfolio demo
"""

import subprocess
import sys
import os
from pathlib import Path

def create_virtual_environment():
    """Create a virtual environment if it doesn't exist"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    print("🔧 Creating virtual environment...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
        print("✅ Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def get_venv_python():
    """Get the path to the virtual environment's Python executable"""
    if os.name == 'nt':  # Windows
        return Path("venv") / "Scripts" / "python.exe"
    else:  # macOS/Linux
        return Path("venv") / "bin" / "python"

def install_requirements_in_venv():
    """Install requirements in the virtual environment"""
    print("📦 Installing demo requirements in virtual environment...")
    
    venv_python = get_venv_python()
    
    try:
        # First install the main requirements
        subprocess.check_call([
            str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"
        ])
        
        # Then install demo-specific requirements
        subprocess.check_call([
            str(venv_python), "-m", "pip", "install", 
            "faker>=19.0.0", "pillow>=10.0.0", "requests>=2.31.0"
        ])
        print("✅ All requirements installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def generate_demo_data_in_venv():
    """Run the demo data generator in the virtual environment"""
    print("🎬 Generating demo data...")
    
    venv_python = get_venv_python()
    
    try:
        subprocess.check_call([str(venv_python), "demo_data_generator.py"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate demo data: {e}")
        return False

def main():
    print("🎯 Flickr Local Browser - Portfolio Demo Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Please run this script from the flickr-downloader-portfolio directory")
        return
    
    # Create virtual environment
    if not create_virtual_environment():
        return
    
    # Install requirements
    if not install_requirements_in_venv():
        return
    
    # Generate demo data
    if not generate_demo_data_in_venv():
        return
    
    print("=" * 50)
    print("🎉 Portfolio demo setup complete!")
    print("\n🚀 To start the demo:")
    print("   source venv/bin/activate")
    print("   python START_FLICKR_BROWSER.py")
    print("\n📝 Demo includes:")
    print("   • 10 realistic photo albums")
    print("   • 400+ demo photos with thumbnails")
    print("   • Realistic metadata and comments")
    print("   • Many-to-many photo-album relationships")

if __name__ == "__main__":
    main()