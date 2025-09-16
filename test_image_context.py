#!/usr/bin/env python3
"""
Test script for image context and association functionality
"""

import requests
import json
import time
from PIL import Image, ImageDraw
import io

BASE_URL = "http://localhost:8000"

def create_test_image():
    """Create a simple test image with identifiable items"""
    # Create a 400x300 image with white background
    img = Image.new('RGB', (400, 300), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw some simple shapes that can be identified
    # Red square
    draw.rectangle([50, 50, 150, 150], fill='red', outline='black', width=2)
    draw.text((75, 160), "Red Square", fill='black')
    
    # Blue circle
    draw.ellipse([200, 50, 300, 150], fill='blue', outline='black', width=2)
    draw.text((215, 160), "Blue Circle", fill='black')
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=90)
    img_bytes.seek(0)
    
    return img_bytes.getvalue()

def test_image_upload_and_analysis():
    """Test image upload and analysis"""
    print("🔄 Testing image upload and analysis...")
    
    # Create test image
    image_data = create_test_image()
    
    # Upload image for conversation analysis
    files = {'file': ('test_image.jpg', image_data, 'image/jpeg')}
    
    try:
        response = requests.post(f"{BASE_URL}/images/analyze-for-conversation", files=files)
        print(f"Upload response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Image uploaded successfully")
            print(f"Image ID: {result['data']['image_id']}")
            print(f"Analysis: {result['data']['analysis']}")
            print(f"Identified items: {result['data']['identified_items']}")
            return result['data']
        else:
            print(f"❌ Upload failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

def test_nlp_command_with_image_context(image_data):
    """Test NLP command with image context"""
    print("\n🔄 Testing NLP command with image context...")
    
    # Prepare the command request with image context
    request_data = {
        "command": "add all these items to bin 100",
        "session_id": "test-session-123",
        "image_context": {
            "image_id": image_data['image_id'],
            "analysis": image_data['analysis'],
            "identified_items": image_data['identified_items']
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/nlp/process-command", json=request_data)
        print(f"NLP command response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ NLP command processed successfully")
            print(f"Response: {result['data']['response']}")
            return result['data']
        else:
            print(f"❌ NLP command failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ NLP command error: {e}")
        return None

def test_bin_contents(bin_id="100"):
    """Test checking bin contents to verify items were added"""
    print(f"\n🔄 Testing bin {bin_id} contents...")

    try:
        # First try using the test endpoint to list all items
        response = requests.get(f"{BASE_URL}/test/list-items")
        print(f"List items response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Items retrieved successfully")
            all_items = result['data']['items']

            # Filter items by bin_id
            items = [item for item in all_items if item.get('bin_id') == bin_id]
            print(f"Items in bin {bin_id}: {len(items)}")

            for item in items:
                print(f"  - {item['name']} (ID: {item['id']})")
                # Check if item has associated images
                if 'images' in item and item['images']:
                    print(f"    📷 Has {len(item['images'])} associated image(s)")
                    for img in item['images']:
                        if isinstance(img, dict):
                            print(f"      Image ID: {img.get('image_id', 'unknown')}")
                        else:
                            print(f"      Image ID: {img}")
                else:
                    print(f"    📷 No associated images")

            return items
        else:
            print(f"❌ Failed to get items: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Bin contents error: {e}")
        return None

def main():
    """Run the complete test suite"""
    print("🚀 Starting Image Context and Association Test Suite")
    print("=" * 60)
    
    # Test 1: Upload and analyze image
    image_data = test_image_upload_and_analysis()
    if not image_data:
        print("❌ Image upload test failed - aborting")
        return
    
    # Test 2: Process NLP command with image context
    nlp_result = test_nlp_command_with_image_context(image_data)
    if not nlp_result:
        print("❌ NLP command test failed - aborting")
        return
    
    # Wait a moment for processing
    print("\n⏳ Waiting for processing to complete...")
    time.sleep(2)
    
    # Test 3: Check bin contents to verify items were added with image associations
    items = test_bin_contents("100")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    if image_data:
        print("✅ Image upload and analysis: PASSED")
        print(f"   - Image ID: {image_data['image_id']}")
        print(f"   - Items identified: {len(image_data['identified_items'])}")
    else:
        print("❌ Image upload and analysis: FAILED")
    
    if nlp_result:
        print("✅ NLP command processing: PASSED")
        print(f"   - Command processed successfully")
    else:
        print("❌ NLP command processing: FAILED")
    
    if items:
        print(f"✅ Bin contents verification: PASSED")
        print(f"   - Items in bin: {len(items)}")
        
        # Check for image associations
        items_with_images = [item for item in items if item.get('images')]
        if items_with_images:
            print(f"✅ Image associations: PASSED")
            print(f"   - Items with images: {len(items_with_images)}")
        else:
            print(f"❌ Image associations: FAILED")
            print(f"   - No items have associated images")
    else:
        print("❌ Bin contents verification: FAILED")
    
    print("\n🏁 Test suite completed!")

if __name__ == "__main__":
    main()
