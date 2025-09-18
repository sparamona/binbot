#!/usr/bin/env python3
"""
Simple test to check if NLP bin commands work after removing upload-to-bin endpoint
"""

import requests
import json
from PIL import Image, ImageDraw
import io

BASE_URL = "http://localhost:8000"

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
            print(f"✅ Server healthy")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_nlp_image_analysis():
    """Test NLP image analysis only"""
    print("\n🔄 Testing NLP image analysis...")
    
    try:
        image_data = create_test_image()
        files = {'image': ('test.jpg', image_data, 'image/jpeg')}
        data = {
            'command': 'what do you see in this image?',
            'session_id': 'test-session'
        }
        
        response = requests.post(f"{BASE_URL}/nlp/command-with-image", files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Image analysis successful!")
                print(f"Response: {result['data'].get('response', 'No response')[:100]}...")
                return True
            else:
                print(f"❌ Image analysis failed: {result}")
                return False
        else:
            print(f"❌ Image analysis HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Image analysis error: {e}")
        return False

def test_nlp_add_to_bin():
    """Test NLP command to add items to bin"""
    print("\n🔄 Testing NLP add to bin command...")
    
    try:
        image_data = create_test_image()
        files = {'image': ('test.jpg', image_data, 'image/jpeg')}
        data = {
            'command': 'add the items you see to bin 99',
            'session_id': 'test-session'
        }
        
        response = requests.post(f"{BASE_URL}/nlp/command-with-image", files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response status: {result.get('success')}")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("✅ Add to bin command successful!")
                return True
            else:
                print("❌ Add to bin command failed")
                return False
        else:
            print(f"❌ Add to bin HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Add to bin error: {e}")
        return False

def test_simple_add_command():
    """Test simple NLP add command without image"""
    print("\n🔄 Testing simple add command...")
    
    try:
        data = {
            'command': 'add red box to bin 99',
            'session_id': 'test-session'
        }
        
        response = requests.post(f"{BASE_URL}/nlp/command", json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("✅ Simple add command successful!")
                return True
            else:
                print("❌ Simple add command failed")
                return False
        else:
            print(f"❌ Simple add HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Simple add error: {e}")
        return False

def main():
    print("🧪 Testing NLP Bin Commands After Upload-to-Bin Removal")
    print("="*60)
    
    # Test 1: Health check
    if not test_health():
        return
    
    # Test 2: Image analysis only
    if not test_nlp_image_analysis():
        return
    
    # Test 3: Add to bin with image
    test_nlp_add_to_bin()
    
    # Test 4: Simple add command
    test_simple_add_command()
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    main()
