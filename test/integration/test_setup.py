#!/usr/bin/env python3
"""
Basic setup test for BinBot project structure
"""

import os
import sys
from pathlib import Path

def test_project_structure():
    """Test that all required directories exist"""
    required_dirs = [
        "api", "chat", "config", "database", "llm", 
        "session", "storage", "utils", "frontend", 
        "data/images", "data/chromadb", "test"
    ]
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"❌ Missing directory: {dir_path}")
            return False
        print(f"✅ Found directory: {dir_path}")
    
    return True

def test_config_files():
    """Test that configuration files exist"""
    required_files = [
        "requirements.txt",
        ".env"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Missing file: {file_path}")
            return False
        print(f"✅ Found file: {file_path}")
    
    return True

def test_python_packages():
    """Test that Python packages are properly structured"""
    package_dirs = ["api", "chat", "config", "database", "llm", "session", "storage", "utils"]
    
    for pkg_dir in package_dirs:
        init_file = os.path.join(pkg_dir, "__init__.py")
        if not os.path.exists(init_file):
            print(f"❌ Missing __init__.py in {pkg_dir}")
            return False
        print(f"✅ Found __init__.py in {pkg_dir}")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing BinBot project setup...")
    print("=" * 50)
    
    all_tests_passed = True
    
    print("\n📁 Testing project structure...")
    all_tests_passed &= test_project_structure()
    
    print("\n📄 Testing configuration files...")
    all_tests_passed &= test_config_files()
    
    print("\n📦 Testing Python packages...")
    all_tests_passed &= test_python_packages()
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 All setup tests passed! Project structure is ready.")
        sys.exit(0)
    else:
        print("❌ Some setup tests failed. Please check the output above.")
        sys.exit(1)
