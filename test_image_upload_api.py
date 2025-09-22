#!/usr/bin/env python3
"""
Test script to directly test the image upload API endpoint
This will help isolate if the issue is in the frontend or backend
"""

import requests
import json
from pathlib import Path

# Configuration
API_BASE = "http://localhost:8000"
TEST_IMAGE = "test/coaster_pen_mouse.jpg"

def test_image_upload_api():
    """Test the complete image upload flow"""
    print("🧪 Testing BinBot Image Upload API")
    print("=" * 50)
    
    # Step 1: Create a session
    print("1️⃣ Creating session...")
    try:
        session_response = requests.post(f"{API_BASE}/api/session")
        if session_response.status_code != 200:
            print(f"❌ Session creation failed: {session_response.status_code}")
            print(f"Response: {session_response.text}")
            return False
        
        session_data = session_response.json()
        session_id = session_data.get('session_id')
        print(f"✅ Session created: {session_id}")
        
        # Get cookies for subsequent requests
        cookies = session_response.cookies
        print(f"🍪 Session cookies: {dict(cookies)}")
        
    except Exception as e:
        print(f"❌ Session creation error: {e}")
        return False
    
    # Step 2: Check if test image exists
    print(f"\n2️⃣ Checking test image: {TEST_IMAGE}")
    image_path = Path(TEST_IMAGE)
    if not image_path.exists():
        print(f"❌ Test image not found: {image_path.absolute()}")
        print("Available test images:")
        test_dir = Path("test")
        if test_dir.exists():
            for img in test_dir.glob("*.jpg"):
                print(f"  - {img}")
        return False
    
    print(f"✅ Test image found: {image_path.absolute()}")
    print(f"📏 Image size: {image_path.stat().st_size} bytes")
    
    # Step 3: Upload image
    print(f"\n3️⃣ Uploading image to /api/chat/image...")
    try:
        with open(image_path, 'rb') as img_file:
            files = {'file': (image_path.name, img_file, 'image/jpeg')}
            
            upload_response = requests.post(
                f"{API_BASE}/api/chat/image",
                files=files,
                cookies=cookies
            )
        
        print(f"📡 Response status: {upload_response.status_code}")
        print(f"📡 Response headers: {dict(upload_response.headers)}")
        
        if upload_response.status_code == 200:
            print("✅ Image upload successful!")
            response_data = upload_response.json()
            print(f"📄 Response data:")
            print(json.dumps(response_data, indent=2))
            
            # Check response structure
            if 'success' in response_data and response_data['success']:
                print(f"🎯 Success: {response_data['success']}")
                print(f"🆔 Image ID: {response_data.get('image_id', 'N/A')}")
                print(f"🔍 Analyzed items: {len(response_data.get('analyzed_items', []))}")
                
                for i, item in enumerate(response_data.get('analyzed_items', []), 1):
                    print(f"  {i}. {item.get('name', 'Unknown')} - {item.get('description', 'No description')}")
                
                return True
            else:
                print(f"❌ Upload marked as failed in response")
                return False
                
        else:
            print(f"❌ Image upload failed: {upload_response.status_code}")
            print(f"📄 Error response: {upload_response.text}")
            
            # Try to parse error details
            try:
                error_data = upload_response.json()
                print(f"🔍 Error details: {json.dumps(error_data, indent=2)}")
            except:
                print("🔍 Could not parse error response as JSON")
            
            return False
            
    except Exception as e:
        print(f"❌ Upload request error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_health_check():
    """Test if the server is running"""
    print("🏥 Testing server health...")
    try:
        health_response = requests.get(f"{API_BASE}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print(f"🔍 Make sure the server is running on {API_BASE}")
        return False

def main():
    """Run all tests"""
    print("🚀 BinBot API Test Suite")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_health_check():
        print("\n❌ Server is not accessible. Please start the BinBot server first.")
        return
    
    print("\n" + "=" * 50)
    
    # Test 2: Image upload
    success = test_image_upload_api()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    if success:
        print("✅ All tests passed! The backend API is working correctly.")
        print("🎯 If the frontend is still failing, the issue is in the JavaScript code.")
    else:
        print("❌ Backend API test failed!")
        print("🎯 The issue is in the backend, not the frontend.")
        print("🔧 Check the server logs for more details.")

if __name__ == "__main__":
    main()
