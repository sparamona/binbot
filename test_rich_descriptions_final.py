#!/usr/bin/env python3
"""
Final test script to verify rich descriptions from vision analysis are stored in database
Tests the pen/coaster/mouse scenario and verifies database storage
"""

import requests
from PIL import Image, ImageDraw
import io
import json
import time

def create_pen_coaster_mouse_image():
    """Create a test image with pen, coaster, and mouse"""
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a red and white pen
    draw.rectangle([50, 50, 180, 70], fill='red', outline='black', width=2)
    draw.rectangle([50, 70, 180, 80], fill='white', outline='black', width=1)
    draw.text((55, 85), 'Red & White Pen', fill='black')
    
    # Draw a cardboard spiral coaster
    draw.ellipse([220, 50, 320, 150], fill='tan', outline='brown', width=3)
    # Add spiral pattern
    for i in range(5):
        radius = 15 + i * 8
        draw.ellipse([270-radius, 100-radius, 270+radius, 100+radius], outline='brown', width=1)
    draw.text([225, 160], 'Cardboard Coaster', fill='black')
    
    # Draw a Logitech wireless mouse
    draw.ellipse([50, 180, 150, 250], fill='darkgray', outline='black', width=2)
    draw.rectangle([90, 190, 110, 210], fill='lightgray', outline='black', width=1)  # scroll wheel
    draw.text([55, 255], 'Logitech Mouse', fill='black')
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes.getvalue()

def test_rich_descriptions_flow():
    """Test the complete flow with rich descriptions"""
    print("=== Testing Rich Descriptions Flow ===")
    
    image_data = create_pen_coaster_mouse_image()
    session_id = f'rich-desc-test-{int(time.time())}'
    bin_id = '9'
    
    # Step 1: Upload image and add items to bin
    print(f"\n1. Uploading image and adding items to bin {bin_id}...")
    files = {'image': ('office_items.jpg', image_data, 'image/jpeg')}
    data = {'command': f'add these items to bin {bin_id}', 'session_id': session_id}
    
    try:
        response = requests.post('http://localhost:8000/nlp/upload-image', files=files, data=data, timeout=90)
        print(f'Upload Status: {response.status_code}')
        if response.status_code == 200:
            result = response.json()
            print(f'Success: {result.get("success")}')
            response_text = result.get("data", {}).get("response", "No response")
            print(f'Response: {response_text}')
            
            if not result.get("success"):
                print("❌ Upload failed, stopping test")
                return False
        else:
            print(f'❌ Upload Error: {response.text}')
            return False
    except Exception as e:
        print(f'❌ Upload Request failed: {e}')
        return False
    
    # Step 2: Wait a moment for processing
    print("\n2. Waiting for processing...")
    time.sleep(2)
    
    # Step 3: Fetch bin contents to verify rich descriptions
    print(f"\n3. Fetching bin {bin_id} contents to verify descriptions...")
    try:
        bin_response = requests.post('http://localhost:8000/nlp/command', 
                                   headers={'Content-Type': 'application/json'},
                                   json={'command': f'what is in bin {bin_id}', 'session_id': session_id}, 
                                   timeout=30)
        print(f'Bin Query Status: {bin_response.status_code}')
        if bin_response.status_code == 200:
            bin_result = bin_response.json()
            print(f'Bin Query Success: {bin_result.get("success")}')
            bin_response_text = bin_result.get("data", {}).get("response", "No response")
            print(f'Bin Contents: {bin_response_text}')
        else:
            print(f'❌ Bin Query Error: {bin_response.text}')
    except Exception as e:
        print(f'❌ Bin Query failed: {e}')
    
    # Step 4: Search database directly to see stored descriptions
    print(f"\n4. Searching database directly for bin {bin_id} items...")
    try:
        search_response = requests.post('http://localhost:8000/search', 
                                      headers={'Content-Type': 'application/json'},
                                      json={'q': f'bin {bin_id}', 'limit': 20}, 
                                      timeout=30)
        print(f'Search Status: {search_response.status_code}')
        if search_response.status_code == 200:
            search_result = search_response.json()
            if search_result.get('success') and search_result.get('data', {}).get('items'):
                items = search_result['data']['items']
                bin_items = [item for item in items if item.get('bin_id') == bin_id]
                
                print(f'\n📦 Found {len(bin_items)} items in bin {bin_id}:')
                print("=" * 80)
                
                for i, item in enumerate(bin_items, 1):
                    name = item.get('name', 'Unknown')
                    description = item.get('description', 'No description')
                    item_id = item.get('item_id', 'Unknown ID')
                    
                    print(f"\n{i}. Item: {name}")
                    print(f"   ID: {item_id}")
                    print(f"   Description: {description}")
                    
                    # Check if this looks like a rich description vs generic
                    if description == f"{name} in bin {bin_id}":
                        print("   ⚠️  GENERIC DESCRIPTION (not using vision analysis)")
                    elif len(description) > 50 and any(word in description.lower() for word in ['color', 'material', 'size', 'brand', 'markings', 'features']):
                        print("   ✅ RICH DESCRIPTION (using vision analysis)")
                    else:
                        print("   ❓ UNCLEAR DESCRIPTION TYPE")
                
                print("=" * 80)
                
                # Summary
                generic_count = sum(1 for item in bin_items if item.get('description', '') == f"{item.get('name', '')} in bin {bin_id}")
                rich_count = len(bin_items) - generic_count
                
                print(f"\n📊 SUMMARY:")
                print(f"   Total items: {len(bin_items)}")
                print(f"   Rich descriptions: {rich_count}")
                print(f"   Generic descriptions: {generic_count}")
                
                if rich_count > 0:
                    print("   ✅ SUCCESS: Rich descriptions are being stored!")
                else:
                    print("   ❌ ISSUE: No rich descriptions found - may need debugging")
                    
            else:
                print('❌ No items found in search results')
        else:
            print(f'❌ Search Error: {search_response.text}')
    except Exception as e:
        print(f'❌ Search failed: {e}')
    
    return True

if __name__ == "__main__":
    print("Testing Rich Descriptions Implementation")
    print("Creating image with pen, coaster, and mouse...")
    
    success = test_rich_descriptions_flow()
    
    if success:
        print("\n🎉 Test completed! Check the results above to see if rich descriptions are working.")
    else:
        print("\n❌ Test failed - server may not be responding correctly")
