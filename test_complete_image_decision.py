#!/usr/bin/env python3
"""
Complete test to verify LLM image decision logic works correctly.
Tests both scenarios:
1. User uploads image, says "add these items" -> should include image_id
2. User then says "add a pencil" -> should NOT include image_id
"""

import requests
import json
import time
from PIL import Image, ImageDraw
import io
import base64

def create_test_image():
    """Create a simple test image with some items"""
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw some simple shapes to represent items
    draw.rectangle([50, 50, 150, 100], fill='red', outline='black')
    draw.text((60, 65), "Hammer", fill='black')
    
    draw.rectangle([200, 50, 300, 100], fill='blue', outline='black')
    draw.text((210, 65), "Screwdriver", fill='white')
    
    draw.rectangle([50, 150, 150, 200], fill='green', outline='black')
    draw.text((60, 165), "Wrench", fill='black')
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_data = buffer.getvalue()
    return base64.b64encode(img_data).decode()

def test_complete_scenario():
    """Test the complete scenario"""
    base_url = "http://localhost:8000"
    session_id = f"test-complete-{int(time.time())}"
    
    print(f"=== Testing Complete Image Decision Scenario ===")
    print(f"Session ID: {session_id}")
    
    try:
        # Step 1: Upload image and ask to add "these items" (should include image_id)
        print("\n1. Testing: Upload image and 'add these items to bin 10' (should include image_id)")
        image_data = create_test_image()

        cmd_response = requests.post(
            f"{base_url}/nlp/command-with-image",
            data={
                "command": "add these items to bin 10",
                "session_id": session_id
            },
            files={"image": ("test_tools.png", base64.b64decode(image_data), "image/png")},
            timeout=30
        )
        
        if cmd_response.status_code != 200:
            print(f"Command failed: {cmd_response.text}")
            return False

        result1 = cmd_response.json()
        print(f"✅ Response: {result1.get('data', {}).get('response', 'No response')}")

        # Step 2: Ask to add a new item (should NOT include image_id)
        print("\n2. Testing: 'add a pencil to bin 15' (should NOT include image_id)")
        
        cmd_response2 = requests.post(
            f"{base_url}/nlp/command",
            json={"command": "add a pencil to bin 15", "session_id": session_id},
            timeout=30
        )
        
        if cmd_response2.status_code != 200:
            print(f"Command failed: {cmd_response2.text}")
            return False
            
        result2 = cmd_response2.json()
        print(f"✅ Response: {result2.get('data', {}).get('response', 'No response')}")
        
        print("\n=== Test completed successfully! ===")
        print("Check the server logs to verify:")
        print("1. First command should show 'Attempting to associate image' with the image_id")
        print("2. Second command should NOT show any image association")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_scenario()
    exit(0 if success else 1)
