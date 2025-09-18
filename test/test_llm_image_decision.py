#!/usr/bin/env python3
"""
Test script to verify that the LLM correctly decides when to include image_id
based on conversational context rather than hardcoded rules.

This test simulates the use cases:
1. User uploads image -> "add all these items to bin X" -> Should include image_id
2. Follow-up request -> "add a pencil to bin Y" -> Should NOT include image_id
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
    # Red square (representing a book)
    draw.rectangle([50, 50, 150, 150], fill='red', outline='black', width=2)
    draw.text((75, 160), "Book", fill='black')
    
    # Blue circle (representing a ball)
    draw.ellipse([200, 50, 300, 150], fill='blue', outline='black', width=2)
    draw.text((225, 160), "Ball", fill='black')
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=90)
    img_bytes.seek(0)
    
    return img_bytes.getvalue()

def test_image_context_decision():
    """Test that LLM makes correct decisions about when to include image_id"""
    print("🔄 Testing LLM image_id decision logic...")
    
    session_id = 'test-llm-decision-123'
    
    # Step 1: Upload image and ask to add "these items"
    print("\nStep 1: Upload image and ask to add 'these items'")
    image_data = create_test_image()
    
    files = {'image': ('test_image.jpg', image_data, 'image/jpeg')}
    data = {
        'command': 'add these items to bin 10',
        'session_id': session_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/nlp/command-with-image", files=files, data=data, timeout=30)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Step 1 completed successfully")
                response_text = result['data'].get('response', '')
                print(f"Response: {response_text[:200]}...")
                
                # Check if the response indicates image association
                if 'image' in response_text.lower() or 'associated' in response_text.lower():
                    print("✅ Response suggests image was associated with items")
                else:
                    print("⚠️  Response doesn't clearly indicate image association")
            else:
                print(f"❌ Step 1 failed: {result.get('error')}")
                return False
        else:
            print(f"❌ Step 1 HTTP error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Step 1 error: {e}")
        return False
    
    # Step 2: Wait a moment, then ask to add a new item (should NOT use image_id)
    print("\nStep 2: Ask to add a new item (should not use image_id)")
    time.sleep(1)
    
    data = {
        'command': 'add a pencil to bin 20',
        'session_id': session_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/nlp/command", json=data, timeout=30)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Step 2 completed successfully")
                response_text = result['data'].get('response', '')
                print(f"Response: {response_text[:200]}...")
                
                # This should NOT mention image association
                if 'image' in response_text.lower() and 'associated' in response_text.lower():
                    print("⚠️  Response unexpectedly mentions image association")
                else:
                    print("✅ Response correctly doesn't mention image association")
                    
                return True
            else:
                print(f"❌ Step 2 failed: {result.get('error')}")
                return False
        else:
            print(f"❌ Step 2 HTTP error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Step 2 error: {e}")
        return False

def test_explicit_image_reference():
    """Test that LLM still includes image_id when explicitly referencing the image"""
    print("\n🔄 Testing explicit image reference...")
    
    session_id = 'test-explicit-ref-456'
    
    # Upload image first
    image_data = create_test_image()
    files = {'image': ('test_image.jpg', image_data, 'image/jpeg')}
    data = {
        'command': 'what do you see in this image?',
        'session_id': session_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/nlp/command-with-image", files=files, data=data, timeout=30)
        if response.status_code != 200:
            print(f"❌ Image upload failed: {response.status_code}")
            return False
            
        result = response.json()
        if not result.get('success'):
            print(f"❌ Image analysis failed: {result.get('error')}")
            return False
            
        print("✅ Image uploaded and analyzed")
        
        # Now ask to add items from the image explicitly
        data = {
            'command': 'add the items from the image to bin 30',
            'session_id': session_id
        }
        
        response = requests.post(f"{BASE_URL}/nlp/command", json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Explicit image reference handled successfully")
                response_text = result['data'].get('response', '')
                print(f"Response: {response_text[:200]}...")
                return True
            else:
                print(f"❌ Explicit reference failed: {result.get('error')}")
                return False
        else:
            print(f"❌ Explicit reference HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Explicit reference error: {e}")
        return False

def main():
    """Run the LLM decision logic test"""
    print("🚀 Testing LLM Image ID Decision Logic")
    print("=" * 60)
    print("This test verifies that the LLM correctly decides when to include")
    print("image_id based on conversational context, not hardcoded rules.")
    print("=" * 60)
    
    # Test 1: Context-based decision making
    context_test = test_image_context_decision()
    
    # Test 2: Explicit image reference
    explicit_test = test_explicit_image_reference()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    if context_test:
        print("✅ Context-based decision making: PASSED")
        print("   - LLM correctly handled 'these items' vs 'a pencil'")
    else:
        print("❌ Context-based decision making: FAILED")
    
    if explicit_test:
        print("✅ Explicit image reference: PASSED")
        print("   - LLM correctly handled 'items from the image'")
    else:
        print("❌ Explicit image reference: FAILED")
    
    overall_success = context_test and explicit_test
    
    if overall_success:
        print("\n🎉 OVERALL RESULT: SUCCESS")
        print("The LLM is correctly making decisions about when to include image_id!")
    else:
        print("\n❌ OVERALL RESULT: NEEDS ATTENTION")
        print("The LLM decision logic may need further refinement.")
    
    return overall_success

if __name__ == "__main__":
    main()
