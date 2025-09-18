#!/usr/bin/env python3
"""
Simple test of the production NLP image endpoint
"""

import requests
from PIL import Image, ImageDraw
import io
import sys

BASE_URL = "http://alpine1.local:8023"

def create_test_image():
    """Create a simple test image"""
    img = Image.new('RGB', (200, 200), 'white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 150, 150], fill='red', outline='black', width=2)
    draw.text((75, 160), "Red Box", fill='black')
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=90)
    img_bytes.seek(0)
    
    return img_bytes.getvalue()

def test_health():
    """Test server health"""
    print("🔄 Testing server health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server healthy - uptime: {data['data']['uptime_seconds']:.0f}s")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_nlp_image():
    """Test NLP with image"""
    print("🔄 Testing NLP image analysis...")

    try:
        # Create test image
        image_data = create_test_image()

        # Send to NLP endpoint
        files = {'image': ('test.jpg', image_data, 'image/jpeg')}
        data = {
            'command': 'what do you see in this image?',
            'session_id': 'test-prod-session'
        }

        print("📤 Sending request...")
        response = requests.post(f"{BASE_URL}/nlp/command-with-image", files=files, data=data, timeout=40)
        
        print(f"📥 Response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ SUCCESS!")
                response_text = result['data'].get('response', 'No response')
                print(f"🤖 AI Response: {response_text[:200]}...")
                return True
            else:
                error = result.get('error', {})
                print(f"❌ FAILED: {error.get('message', 'Unknown error')}")
                print(f"Error type: {error.get('type', 'Unknown')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Raw response: {response.text[:500]}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Request timed out (>40 seconds)")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Production NLP Image Test")
    print(f"🎯 Target: {BASE_URL}")
    print("="*40)
    
    # Test health first
    if not test_health():
        print("❌ Server not healthy, aborting test")
        sys.exit(1)
    
    print()
    
    # Test image analysis
    success = test_nlp_image()
    
    print("\n" + "="*40)
    if success:
        print("🎉 Production image analysis is WORKING!")
    else:
        print("❌ Production image analysis needs attention")
    
    print("🏁 Test completed!")
