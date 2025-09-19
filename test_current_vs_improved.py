#!/usr/bin/env python3
"""
Test script to compare current behavior vs improved behavior for rich descriptions
"""

import requests
from PIL import Image, ImageDraw
import io
import json

def create_test_image():
    """Create a test image with detailed items"""
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a detailed red screwdriver
    draw.rectangle([50, 50, 180, 80], fill='red', outline='black', width=2)
    draw.text((60, 60), 'CRAFTSMAN', fill='white')
    draw.text((55, 85), 'Screwdriver', fill='black')
    
    # Draw a detailed blue wrench
    draw.rectangle([220, 120, 350, 150], fill='blue', outline='black', width=2)
    draw.text((230, 130), 'STANLEY', fill='white')
    draw.text((225, 155), 'Adjustable Wrench', fill='black')
    
    # Add some wear marks
    draw.line([(60, 75), (70, 75)], fill='darkred', width=2)
    draw.line([(240, 145), (250, 145)], fill='darkblue', width=2)
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes.getvalue()

def test_current_behavior():
    """Test the current system behavior"""
    print("=== Testing Current System Behavior ===")
    
    image_data = create_test_image()
    
    # Test 1: Upload image and ask what's in it
    print("\n1. Uploading image and asking about content...")
    files = {'image': ('detailed_tools.jpg', image_data, 'image/jpeg')}
    data = {'command': 'What tools can you see in this image?', 'session_id': 'current-behavior-test'}
    
    try:
        response = requests.post('http://localhost:8000/nlp/upload-image', files=files, data=data, timeout=60)
        print(f'Status: {response.status_code}')
        if response.status_code == 200:
            result = response.json()
            print(f'Success: {result.get("success")}')
            print(f'Response: {result.get("data", {}).get("response", "No response")}')
        else:
            print(f'Error: {response.text}')
    except Exception as e:
        print(f'Request failed: {e}')
        return False
    
    # Test 2: Add items from the image
    print("\n2. Adding items from the uploaded image...")
    data2 = {'command': 'add these tools to bin 7', 'session_id': 'current-behavior-test'}
    
    try:
        response2 = requests.post('http://localhost:8000/nlp/command', 
                                 headers={'Content-Type': 'application/json'}, 
                                 json=data2, timeout=60)
        print(f'Status: {response2.status_code}')
        if response2.status_code == 200:
            result2 = response2.json()
            print(f'Success: {result2.get("success")}')
            print(f'Response: {result2.get("data", {}).get("response", "No response")}')
        else:
            print(f'Error: {response2.text}')
    except Exception as e:
        print(f'Request failed: {e}')
        return False
    
    # Test 3: Check what was actually stored in the database
    print("\n3. Checking what was stored in the database...")
    try:
        search_response = requests.post('http://localhost:8000/search', 
                                      headers={'Content-Type': 'application/json'},
                                      json={'q': 'bin 7', 'limit': 10}, timeout=30)
        print(f'Search Status: {search_response.status_code}')
        if search_response.status_code == 200:
            search_result = search_response.json()
            if search_result.get('success') and search_result.get('data', {}).get('items'):
                items = search_result['data']['items']
                print(f'Found {len(items)} items in bin 7:')
                for item in items:
                    name = item.get('name', 'Unknown')
                    description = item.get('description', 'No description')
                    print(f'  • {name}: {description}')
            else:
                print('No items found or search failed')
        else:
            print(f'Search Error: {search_response.text}')
    except Exception as e:
        print(f'Search failed: {e}')
    
    return True

def test_vision_analysis_details():
    """Test what the vision service actually returns"""
    print("\n=== Testing Vision Service Analysis ===")
    
    image_data = create_test_image()
    
    # Upload image to get analysis
    files = {'image': ('vision_test.jpg', image_data, 'image/jpeg')}
    data = {'command': 'What do you see?', 'session_id': 'vision-analysis-test'}
    
    try:
        response = requests.post('http://localhost:8000/nlp/upload-image', files=files, data=data, timeout=60)
        print(f'Vision Analysis Status: {response.status_code}')
        if response.status_code == 200:
            result = response.json()
            print(f'Success: {result.get("success")}')
            response_text = result.get("data", {}).get("response", "No response")
            print(f'Vision Response: {response_text}')
            
            # The response should contain the detailed analysis
            if "screwdriver" in response_text.lower() or "wrench" in response_text.lower():
                print("✅ Vision service is identifying items correctly")
            else:
                print("⚠️  Vision service may not be identifying items as expected")
        else:
            print(f'Error: {response.text}')
    except Exception as e:
        print(f'Vision analysis failed: {e}')

if __name__ == "__main__":
    print("Testing Current System vs Improved Rich Descriptions")
    print("=" * 60)
    
    # Test current behavior
    success = test_current_behavior()
    
    if success:
        # Test vision analysis details
        test_vision_analysis_details()
        
        print("\n" + "=" * 60)
        print("ANALYSIS:")
        print("- Current system should show generic descriptions like 'item_name in bin X'")
        print("- Improved system would show rich descriptions from vision analysis")
        print("- The vision service is providing detailed analysis, but it's not being stored")
        print("- Our improvements will capture and use these rich descriptions")
    else:
        print("❌ Tests failed - server may not be responding correctly")
