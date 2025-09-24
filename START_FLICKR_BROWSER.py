#!/usr/bin/env python3
"""
Flickr Local Browser - Easy Startup Script
This script tries multiple ways to start the application
"""

import subprocess
import sys
import os
from pathlib import Path

def find_python():
    """Try to find a working Python installation"""
    python_candidates = [
        sys.executable,  # Current Python
        "./venv/bin/python",  # Virtual env Python
        "./venv/bin/python3",  # Virtual env Python3
        "python3",  # System Python3
        "python",   # System Python
        "/usr/bin/python3",  # Standard system location
        "/usr/local/bin/python3",  # Homebrew location
    ]
    
    for python_path in python_candidates:
        try:
            # Test if this Python works
            result = subprocess.run([python_path, "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Found working Python: {python_path}")
                return python_path
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    return None

def main():
    print("=" * 55)
    print("🚀 Starting Flickr Local Browser...")
    print("=" * 55)
    
    # Change to the script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check if required files exist
    launcher_file = script_dir / "src" / "launcher.py"
    if not launcher_file.exists():
        print(f"❌ Required files not found in {script_dir}")
        print("Make sure all files are in the correct location.")
        input("Press Enter to exit...")
        return
    
    print("✅ All required files found")
    
    # Try to find a working Python
    python_path = find_python()
    
    if not python_path:
        print("❌ No working Python installation found!")
        print("")
        print("💡 SOLUTIONS:")
        print("1. Try double-clicking 'EASY_START.command' instead")
        print("2. Or install Python from https://python.org")
        print("")
        input("Press Enter to exit...")
        return
    
    print("🌐 Opening Flickr Local Browser...")
    print("📱 Your browser should open automatically")
    print("")
    print("💡 If the browser doesn't open, go to: http://127.0.0.1:9000")
    print("")
    print("⚠️  Keep this window open while using the browser")
    print("🛑 To stop the application, close this window or press Ctrl+C")
    print("=" * 55)
    
    try:
        # Run the launcher with the found Python
        subprocess.run([python_path, str(launcher_file)])
    except KeyboardInterrupt:
        print("\n👋 Flickr Local Browser stopped by user")
    except FileNotFoundError:
        print("\n❌ Python executable not found.")
        print("This usually means Python isn't installed or isn't in PATH.")
        print("\n💡 Try using the EASY_START.command file instead.")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        print("\n💡 Try using the EASY_START.command file instead.")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
