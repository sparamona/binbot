#!/usr/bin/env python3
"""
End-to-end test for complete image workflow:
1. Upload image via /api/chat/image
2. Use chat API to add items to a random bin
3. Verify bin contents include descriptions and image associations
"""

import requests
import json
import random
import string
from pathlib import Path


def generate_random_bin_id():
    """Generate a random bin ID like 'A3', 'B7', etc."""
    letter = random.choice(string.ascii_uppercase)
    number = random.randint(1, 9)
    return f"{letter}{number}"


def test_complete_image_workflow():
    """Test the complete image workflow from upload to bin storage"""
    
    print("🧪 Testing Complete Image Workflow")
    print("=" * 50)
    
    base_url = "http://localhost:8001"
    test_image = "test/coaster_pen_mouse.jpg"
    
    # Check if test image exists
    if not Path(test_image).exists():
        print(f"❌ Test image not found: {test_image}")
        return False
    
    try:
        # Step 1: Create session
        print("\n1️⃣ Creating session...")
        session_resp = requests.post(f"{base_url}/api/session")
        if session_resp.status_code != 200:
            print(f"❌ Session creation failed: {session_resp.status_code}")
            return False
        
        cookies = session_resp.cookies
        session_data = session_resp.json()
        session_id = session_data['session_id']
        print(f"✅ Session created: {session_id[:8]}...")
        
        # Step 2: Upload and analyze image
        print("\n2️⃣ Uploading and analyzing image...")
        with open(test_image, "rb") as f:
            files = {"file": ("coaster_pen_mouse.jpg", f, "image/jpeg")}
            upload_resp = requests.post(
                f"{base_url}/api/chat/image", 
                files=files, 
                cookies=cookies
            )
        
        if upload_resp.status_code != 200:
            print(f"❌ Image upload failed: {upload_resp.status_code}")
            print(f"Response: {upload_resp.text}")
            return False
        
        upload_data = upload_resp.json()
        image_id = upload_data['image_id']
        analyzed_items = upload_data['analyzed_items']
        
        print(f"✅ Image uploaded and analyzed")
        print(f"📷 Image ID: {image_id}")
        print(f"🔍 Found {len(analyzed_items)} items:")
        for i, item in enumerate(analyzed_items, 1):
            print(f"   {i}. {item['name']} - {item['description'][:50]}...")
        
        # Step 3: Generate random bin ID and add items via chat
        bin_id = generate_random_bin_id()
        print(f"\n3️⃣ Adding items to bin {bin_id} via chat...")
        
        chat_message = f"add them to bin {bin_id}"
        chat_payload = {"message": chat_message}
        
        chat_resp = requests.post(
            f"{base_url}/api/chat/command",
            json=chat_payload,
            cookies=cookies
        )
        
        if chat_resp.status_code != 200:
            print(f"❌ Chat request failed: {chat_resp.status_code}")
            print(f"Response: {chat_resp.text}")
            return False
        
        chat_data = chat_resp.json()
        print(f"✅ Chat response: {chat_data['response'][:100]}...")
        
        # Step 4: Retrieve bin contents and verify
        print(f"\n4️⃣ Retrieving contents of bin {bin_id}...")
        
        bin_resp = requests.get(f"{base_url}/api/inventory/bin/{bin_id}")
        
        if bin_resp.status_code != 200:
            print(f"❌ Bin retrieval failed: {bin_resp.status_code}")
            print(f"Response: {bin_resp.text}")
            return False
        
        bin_data = bin_resp.json()
        bin_items = bin_data.get('items', [])
        
        print(f"✅ Retrieved bin contents")
        print(f"📦 Bin {bin_id} contains {len(bin_items)} items:")
        
        # Step 5: Verify each item has description and image association
        print(f"\n5️⃣ Verifying item details...")
        
        success = True
        for i, item in enumerate(bin_items, 1):
            print(f"\n   Item {i}: {item.get('name', 'Unknown')}")
            description = item.get('description', 'No description')
            if description and description != '...':
                print(f"   📝 Description: {description}")
            else:
                print(f"   📝 Description: {description} (TRUNCATED OR MISSING)")
            print(f"   🆔 Item ID: {item.get('id', 'No ID')}")
            print(f"   📷 Image ID: {item.get('image_id', 'No image')}")
            
            # Verify required fields
            if not item.get('description'):
                print(f"   ❌ Missing description")
                success = False
            else:
                print(f"   ✅ Has description")
            
            if not item.get('image_id'):
                print(f"   ❌ Missing image association")
                success = False
            elif item.get('image_id') == image_id:
                print(f"   ✅ Correctly associated with uploaded image")
            else:
                print(f"   ⚠️ Associated with different image: {item.get('image_id')}")
        
        # Step 6: Final verification
        print(f"\n6️⃣ Final verification...")
        
        if len(bin_items) != len(analyzed_items):
            print(f"❌ Item count mismatch: expected {len(analyzed_items)}, got {len(bin_items)}")
            success = False
        else:
            print(f"✅ Item count matches: {len(bin_items)} items")
        
        if success:
            print(f"\n🎉 Complete workflow test PASSED!")
            print(f"✅ Image uploaded and analyzed successfully")
            print(f"✅ Items added to bin {bin_id} via chat")
            print(f"✅ All items have descriptions and image associations")
            return True
        else:
            print(f"\n❌ Complete workflow test FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_complete_image_workflow()
    exit(0 if success else 1)
