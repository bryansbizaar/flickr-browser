#!/usr/bin/env python3
"""
Test runner for Flickr Local Browser
"""

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Run the complete test suite"""
    print("🧪 Running Flickr Local Browser Tests")
    print("=" * 50)
    
    # Change to project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Check if pytest is available
    try:
        import pytest
        print("✅ pytest is available")
    except ImportError:
        print("❌ pytest not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest"])
        print("✅ pytest installed")
    
    # Run all tests
    print("\n🧪 Running all tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/", 
        "-v", 
        "--tb=short"
    ], capture_output=False)
    
    if result.returncode == 0:
        print("\n🎉 All tests passed! Your portfolio project has professional-grade testing.")
        return True
    else:
        print("\n❌ Some tests failed. Check output above for details.")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
