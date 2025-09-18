#!/usr/bin/env python3
"""
Debug test to see what's happening with vision analysis
"""

import requests
import json

BASE_URL = "http://localhost:8000"
IMAGE_PATH = "test/coaster_pen_mouse.jpg"

def test_vision_analysis():
    """Test vision analysis with detailed debugging"""
    print(f"🔄 Testing vision analysis with {IMAGE_PATH}...")
    
    try:
        # Read the image file
        with open(IMAGE_PATH, 'rb') as img_file:
            image_data = img_file.read()
        
        print(f"✅ Image loaded: {len(image_data)} bytes")
        
        # Send to NLP endpoint with a very specific command
        files = {'image': ('coaster_pen_mouse.jpg', image_data, 'image/jpeg')}
        data = {
            'command': 'describe everything you can see in this image in detail',
            'session_id': 'debug-vision-test'
        }
        
        print("📤 Sending detailed analysis request...")
        response = requests.post(f"{BASE_URL}/nlp/command-with-image", files=files, data=data, timeout=60)
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Response received!")
            print(f"📋 Full response structure:")
            print(json.dumps(result, indent=2))
            
            if result.get('success'):
                response_text = result['data'].get('response', 'No response')
                print(f"\n🤖 AI Response Text:")
                print(f"'{response_text}'")
                print(f"\nResponse length: {len(response_text)} characters")
                
                # Check if it's a generic response
                if "operation completed successfully" in response_text.lower():
                    print("⚠️  Got generic response - vision analysis may not be working")
                else:
                    print("✅ Got detailed response - vision analysis is working")
                    
            else:
                error = result.get('error', {})
                print(f"❌ Request failed: {error}")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_simple_nlp():
    """Test simple NLP without image"""
    print("\n🔄 Testing simple NLP command...")
    
    try:
        data = {
            'command': 'help me understand what you can do',
            'session_id': 'debug-simple-test'
        }
        
        response = requests.post(f"{BASE_URL}/nlp/command", json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                response_text = result['data'].get('response', 'No response')
                print(f"✅ Simple NLP working: {response_text[:100]}...")
            else:
                print(f"❌ Simple NLP failed: {result.get('error')}")
        else:
            print(f"❌ Simple NLP HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Simple NLP exception: {e}")

if __name__ == "__main__":
    print("🚀 Vision Analysis Debug Test")
    print("="*50)
    
    # Test simple NLP first
    test_simple_nlp()
    
    # Test vision analysis
    test_vision_analysis()
    
    print("\n🏁 Debug test completed!")
