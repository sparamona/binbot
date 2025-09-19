#!/usr/bin/env python3
"""
Test script to verify image upload functionality works with refactored LLM
"""

import requests
import json
import time
from io import BytesIO
from PIL import Image

def create_test_image():
    """Create a simple test image"""
    # Create a simple red rectangle with text
    img = Image.new('RGB', (200, 100), color='red')
    
    # Save to bytes
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()

def test_health():
    """Test server health"""
    print("🔄 Testing server health...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Server is healthy!")
            print(f"   Status: {data.get('status')}")
            
            services = data.get('services', {})
            for service, status in services.items():
                print(f"   {service}: {status}")
            
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_image_upload_with_command():
    """Test image upload with command processing"""
    print("\n🔄 Testing image upload with command...")
    
    try:
        # Create test image
        image_data = create_test_image()
        
        # Prepare form data
        files = {
            'image': ('test_image.jpg', image_data, 'image/jpeg')
        }
        
        data = {
            'command': 'analyze this image and add any items you find to bin 5',
            'session_id': 'test-image-upload-session'
        }
        
        print("📤 Uploading image with command...")
        
        response = requests.post(
            "http://localhost:8000/nlp/upload-image",
            files=files,
            data=data,
            timeout=60
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Image upload successful!")
            
            # Pretty print the response
            print("\n📋 Response:")
            print(json.dumps(result, indent=2))
            
            if result.get('success'):
                response_data = result.get('data', {})
                message = response_data.get('message', 'No message')
                print(f"\n💬 Bot Response: {message}")
                return True
            else:
                error = result.get('error', {})
                print(f"\n❌ Upload failed: {error}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Image upload error: {e}")
        return False

def test_simple_image_command():
    """Test a simple image command without actual upload"""
    print("\n🔄 Testing simple image-related command...")
    
    try:
        url = "http://localhost:8000/nlp/command"
        payload = {
            "command": "I want to upload an image, how does it work?",
            "session_id": "test-image-help-session"
        }
        
        print(f"📤 Sending: {payload['command']}")
        
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Simple command successful!")
            
            if data.get('success'):
                response_data = data.get('data', {})
                message = response_data.get('message', 'No response message')
                print(f"💬 Bot Response: {message}")
                return True
            else:
                error = data.get('error', {})
                print(f"❌ Command failed: {error}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Simple command error: {e}")
        return False

def main():
    """Run the image upload tests"""
    print("🚀 Testing Image Upload with Refactored LLM")
    print("=" * 50)
    
    # Test health first
    if not test_health():
        print("\n❌ Server health check failed. Is the server running?")
        return False
    
    # Test simple command first
    if not test_simple_image_command():
        print("\n❌ Simple command failed. Check server logs.")
        return False
    
    # Test image upload
    if test_image_upload_with_command():
        print("\n🎉 Image upload test completed successfully!")
        print("✅ The refactored LLM integration works with image uploads!")
    else:
        print("\n⚠️  Image upload failed. This was the original issue we were fixing.")
        print("💡 Check the server logs for more details.")
    
    return True

if __name__ == "__main__":
    main()
