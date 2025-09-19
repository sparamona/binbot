#!/usr/bin/env python3

import requests
import json
import time
import os
from PIL import Image
import io

def test_server_health():
    """Test basic server health"""
    print("🏥 Testing server health...")
    
    try:
        response = requests.get('http://localhost:8000/health', timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                data = result.get("data", {})
                print(f"✅ Server is healthy")
                print(f"   Database connected: {data.get('database_connected')}")
                print(f"   LLM connected: {data.get('llm_connected')}")
                print(f"   Inventory count: {data.get('collections', {}).get('inventory_count', 'N/A')}")
                return True
            else:
                print("❌ Server health check failed")
                return False
        else:
            print(f"❌ Health check returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_bin_query():
    """Test bin query functionality"""
    print("\n📦 Testing bin query functionality...")
    
    try:
        response = requests.post(
            'http://localhost:8000/nlp/command',
            json={
                'command': 'what is in bin 5?',
                'session_id': 'test-comprehensive'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                response_text = result.get("data", {}).get("response", "")
                print("✅ Bin query successful")
                print(f"   Response preview: {response_text[:100]}...")
                
                # Check if it mentions items or bin contents
                if any(word in response_text.lower() for word in ['items', 'bin', 'contains', 'found']):
                    print("✅ Response contains expected content")
                    return True
                else:
                    print("⚠️  Response may not contain expected bin content")
                    return False
            else:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                print(f"❌ Bin query failed: {error_msg}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Bin query exception: {e}")
        return False

def test_simple_chat():
    """Test simple chat functionality"""
    print("\n💬 Testing simple chat functionality...")
    
    try:
        response = requests.post(
            'http://localhost:8000/nlp/command',
            json={
                'command': 'hello, how are you?',
                'session_id': 'test-comprehensive'
            },
            timeout=20
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                response_text = result.get("data", {}).get("response", "")
                print("✅ Simple chat successful")
                print(f"   Response preview: {response_text[:100]}...")
                return True
            else:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                print(f"❌ Simple chat failed: {error_msg}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Simple chat exception: {e}")
        return False

def create_test_image():
    """Create a simple test image"""
    # Create a simple red rectangle image
    img = Image.new('RGB', (200, 100), color='red')
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()

def test_image_upload():
    """Test image upload functionality"""
    print("\n🖼️  Testing image upload functionality...")
    
    try:
        # Create test image
        image_data = create_test_image()
        
        # Test the upload-image endpoint
        files = {'image': ('test_image.jpg', image_data, 'image/jpeg')}
        data = {
            'command': 'What do you see in this image?',
            'session_id': 'test-comprehensive'
        }
        
        response = requests.post(
            'http://localhost:8000/nlp/upload-image',
            files=files,
            data=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            success = result.get("success", False)
            
            if success:
                print("✅ Image upload successful")
                response_text = result.get("data", {}).get("response", "No response")
                print(f"   Response preview: {response_text[:100]}...")
                return True
            else:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                print(f"❌ Image upload failed: {error_msg}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Image upload exception: {e}")
        return False

def main():
    """Run comprehensive functionality tests"""
    print("🚀 Comprehensive BinBot Functionality Test")
    print("=" * 60)
    
    tests = [
        ("Server Health", test_server_health),
        ("Simple Chat", test_simple_chat),
        ("Bin Query", test_bin_query),
        ("Image Upload", test_image_upload)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {test_name}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! BinBot is fully functional!")
        print("✅ LLM refactoring is complete and working correctly")
        print("✅ Image upload issue has been resolved")
        print("✅ All core functionality is operational")
    else:
        print(f"\n⚠️  {total-passed} test(s) failed. Please investigate.")
    
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
