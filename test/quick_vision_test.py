#!/usr/bin/env python3
"""
Quick test to verify vision service is working after cleanup
"""

import requests
import os

def test_vision_quick():
    """Quick test of vision service"""
    print("🔍 Quick Vision Service Test")
    print("="*40)
    
    # Check if app is running
    try:
        health = requests.get("http://localhost:8000/health", timeout=5)
        if health.status_code == 200:
            print("✅ Application is running")
        else:
            print("❌ Application not responding")
            return False
    except:
        print("❌ Cannot connect to application")
        return False
    
    # Test with small optimized image
    test_image_path = "test/coaster_pen_mouse.jpg"
    
    if not os.path.exists(test_image_path):
        print(f"❌ Test image not found: {test_image_path}")
        return False
    
    # Get image size
    with open(test_image_path, 'rb') as f:
        image_data = f.read()
    
    print(f"📁 Using optimized test image: {len(image_data):,} bytes")
    
    try:
        print("🔄 Testing NLP with image...")
        
        with open(test_image_path, 'rb') as f:
            files = {'image': ('test.jpg', f, 'image/jpeg')}
            data = {
                'command': 'What do you see?',
                'session_id': 'quick-test'
            }
            
            response = requests.post(
                "http://localhost:8000/nlp/command-with-image",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                items = result.get("data", {}).get("identified_items", [])
                print(f"✅ Success! Found {len(items)} items:")
                for item in items[:3]:  # Show first 3
                    print(f"   • {item.get('name', 'Unknown')}")
                return True
            else:
                print(f"❌ API returned error: {result}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_vision_quick()
    if success:
        print("\n🎉 Vision service is working perfectly after cleanup!")
    else:
        print("\n❌ Vision service test failed")
    exit(0 if success else 1)
