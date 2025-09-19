#!/usr/bin/env python3

import requests
import json
import time
import os
from PIL import Image
import io

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
    """Test the image upload functionality that was previously failing"""
    print("🧪 Testing Image Upload Fix...")
    
    try:
        # Create test image
        image_data = create_test_image()
        
        # Test the upload-image endpoint that was failing
        files = {'image': ('test_image.jpg', image_data, 'image/jpeg')}
        data = {
            'command': 'What do you see in this image?',
            'session_id': 'test-upload-fix'
        }
        
        print("📤 Uploading image to /nlp/upload-image endpoint...")
        start_time = time.time()
        
        response = requests.post(
            'http://localhost:8000/nlp/upload-image',
            files=files,
            data=data,
            timeout=60
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Request completed in {duration:.1f}s")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            success = result.get("success", False)
            
            if success:
                print("✅ SUCCESS! Image upload is working correctly!")
                
                # Check if we got a response
                response_text = result.get("data", {}).get("response", "No response")
                print(f"💬 Response preview: {response_text[:100]}...")
                
                # Check if image was analyzed
                if "image" in response_text.lower() or "see" in response_text.lower():
                    print("🔍 Image analysis appears to be working!")
                else:
                    print("⚠️  Image analysis may not be working as expected")
                    
                return True
            else:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                print(f"❌ FAILED: {error_msg}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return False

def test_basic_health():
    """Test basic server health"""
    print("🏥 Testing server health...")
    
    try:
        response = requests.get('http://localhost:8000/health', timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Server is healthy")
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

if __name__ == "__main__":
    print("🚀 Testing Image Upload Fix")
    print("=" * 50)
    
    # Test server health first
    if not test_basic_health():
        print("❌ Server is not healthy, aborting tests")
        exit(1)
    
    print()
    
    # Test image upload
    success = test_image_upload()
    
    print()
    print("=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED! Image upload issue has been fixed!")
    else:
        print("💥 TESTS FAILED! Image upload issue persists")
        
    print("=" * 50)
