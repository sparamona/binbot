#!/usr/bin/env python3
"""
Simple test runner for BinBot test suite
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_test(test_path, description=""):
    """Run a single test and return success status"""
    print(f"🧪 Running: {test_path}")
    if description:
        print(f"   {description}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run([
            sys.executable, str(test_path)
        ], cwd=project_root, capture_output=True, text=True, timeout=60,
        encoding='utf-8', errors='replace')
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"   ✅ PASSED ({duration:.1f}s)")
            return True
        else:
            print(f"   ❌ FAILED ({duration:.1f}s)")
            if result.stdout:
                print("   STDOUT:", result.stdout[-200:])  # Last 200 chars
            if result.stderr:
                print("   STDERR:", result.stderr[-200:])  # Last 200 chars
            return False
            
    except subprocess.TimeoutExpired:
        print(f"   ⏰ TIMEOUT (60s)")
        return False
    except Exception as e:
        print(f"   💥 ERROR: {e}")
        return False

def main():
    """Run test suite with different modes"""
    
    print("🚀 BinBot Test Suite")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        mode = "quick"
    
    test_root = project_root / "test"
    passed = 0
    total = 0
    
    if mode == "quick":
        print("🏃 Quick Test Mode - Essential tests only")
        print()
        
        tests = [
            (test_root / "integration" / "test_end_to_end_memory.py", "Complete system validation"),
            (test_root / "unit" / "test_chromadb.py", "Database functionality"),
            (test_root / "unit" / "test_session.py", "Session management"),
        ]
        
    elif mode == "unit":
        print("🔧 Unit Test Mode - Component tests")
        print()
        
        unit_dir = test_root / "unit"
        tests = [
            (f, f"Unit test: {f.stem}") 
            for f in unit_dir.glob("test_*.py")
        ]
        
    elif mode == "integration":
        print("🔗 Integration Test Mode - Multi-component tests")
        print()
        
        integration_dir = test_root / "integration"
        tests = [
            (f, f"Integration test: {f.stem}") 
            for f in integration_dir.glob("test_*.py")
        ]
        
    elif mode == "analysis":
        print("📊 Analysis Mode - Research and tuning scripts")
        print()
        
        analysis_dir = test_root / "analysis"
        tests = [
            (f, f"Analysis: {f.stem}") 
            for f in analysis_dir.glob("test_*.py")
        ]
        
    elif mode == "all":
        print("🌟 Full Test Suite - All tests")
        print()
        
        tests = []
        for subdir in ["unit", "integration", "analysis"]:
            subdir_path = test_root / subdir
            tests.extend([
                (f, f"{subdir.title()}: {f.stem}") 
                for f in subdir_path.glob("test_*.py")
            ])
    
    else:
        print(f"❌ Unknown mode: {mode}")
        print("Available modes: quick, unit, integration, analysis, all")
        return 1
    
    # Run tests
    for test_path, description in tests:
        total += 1
        if run_test(test_path, description):
            passed += 1
        print()
    
    # Summary
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️ {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
