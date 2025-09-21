#!/usr/bin/env python3
"""
Simple test to check if the issue is frontend or backend
"""

print("🧪 Testing BinBot API")

try:
    import requests
    print("✅ Requests module available")
except ImportError:
    print("❌ Requests module not available")
    exit(1)

# Test server connection
try:
    print("🏥 Testing server connection...")
    response = requests.get("http://localhost:8001/health", timeout=5)
    print(f"✅ Server responded: {response.status_code}")
    print(f"📄 Response: {response.text}")
except Exception as e:
    print(f"❌ Server connection failed: {e}")
    print("🔍 Make sure the BinBot server is running on http://localhost:8001")
    exit(1)

# Test session creation
try:
    print("\n🔐 Testing session creation...")
    response = requests.post("http://localhost:8001/api/session")
    print(f"✅ Session response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"📄 Session data: {data}")
        cookies = response.cookies
        print(f"🍪 Cookies: {dict(cookies)}")
    else:
        print(f"❌ Session creation failed: {response.text}")
        exit(1)
except Exception as e:
    print(f"❌ Session creation error: {e}")
    exit(1)

# Test image upload
try:
    print("\n📷 Testing image upload...")
    
    # Check if test image exists
    import os
    test_image = "test/coaster_pen_mouse.jpg"
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        # Try to find any image in test directory
        if os.path.exists("test"):
            images = [f for f in os.listdir("test") if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if images:
                test_image = f"test/{images[0]}"
                print(f"🔄 Using alternative image: {test_image}")
            else:
                print("❌ No test images found")
                exit(1)
        else:
            print("❌ Test directory not found")
            exit(1)
    
    print(f"✅ Using test image: {test_image}")
    
    # Upload the image
    with open(test_image, 'rb') as f:
        files = {'file': (os.path.basename(test_image), f, 'image/jpeg')}
        response = requests.post(
            "http://localhost:8001/api/chat/image",
            files=files,
            cookies=cookies
        )
    
    print(f"📡 Upload response: {response.status_code}")
    print(f"📄 Response text: {response.text}")
    
    if response.status_code == 200:
        print("✅ Image upload successful!")
        data = response.json()
        print(f"🎯 Analysis found {len(data.get('analyzed_items', []))} items")
    else:
        print(f"❌ Image upload failed with status {response.status_code}")
        print("🔍 This indicates a BACKEND issue, not frontend")
        
except Exception as e:
    print(f"❌ Image upload error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Test complete")
