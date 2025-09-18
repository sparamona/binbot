#!/usr/bin/env python3
"""
Simple test of the NLP image endpoint
"""

import requests
from PIL import Image, ImageDraw
import io

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

def test_nlp_image():
    """Test NLP with image"""
    print("🔄 Testing NLP image analysis...")
    
    # Create test image
    image_data = create_test_image()
    
    # Send to NLP endpoint
    files = {'image': ('test.jpg', image_data, 'image/jpeg')}
    data = {
        'command': 'what do you see in this image?',
        'session_id': 'test-session'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/nlp/command-with-image", files=files, data=data, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ SUCCESS!")
                print(f"Response: {result['data'].get('response', 'No response')}")
                return True
            else:
                error = result.get('error', {})
                print(f"❌ FAILED: {error.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Simple NLP Image Test")
    print("="*30)
    
    success = test_nlp_image()
    
    if success:
        print("\n🎉 Image analysis through NLP path is WORKING!")
    else:
        print("\n❌ Image analysis through NLP path needs attention")
    
    print("\n🏁 Test completed!")
