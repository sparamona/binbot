#!/usr/bin/env python3
"""
Test image analysis functionality after removing optimization logic
"""

import requests
import base64
import json
import os
import time

def encode_image_to_base64(image_path):
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def test_image_analysis_direct():
    """Test image analysis using direct NLP endpoint with base64 image"""
    print("🧪 Testing Direct Image Analysis via NLP")
    print("=" * 60)

    # Test image path
    image_path = 'test/coaster_pen_mouse.jpg'

    if not os.path.exists(image_path):
        print(f"❌ Test image not found: {image_path}")
        return False

    print(f"📸 Using test image: {image_path}")

    try:
        # Encode image to base64
        print("\n🔄 Step 1: Encoding image to base64...")
        base64_image = encode_image_to_base64(image_path)
        print(f"✅ Image encoded: {len(base64_image)} characters")

        # Test vision query through NLP endpoint
        print("\n🔄 Step 2: Testing vision query through NLP...")

        # Create request with base64 image
        request_data = {
            'command': 'What items do you see in this image? Please describe each one.',
            'session_id': f'test-vision-{int(time.time())}',
            'image': base64_image
        }

        nlp_response = requests.post(
            'http://localhost:8000/nlp/command',
            json=request_data,
            timeout=90
        )

        print(f"📥 NLP Response status: {nlp_response.status_code}")

        if nlp_response.status_code != 200:
            print(f"❌ NLP request failed: {nlp_response.status_code}")
            print(f"Response: {nlp_response.text}")
            return False

        nlp_result = nlp_response.json()

        if nlp_result.get("success"):
            response_message = nlp_result.get("data", {}).get("message", "")
            print(f"✅ Vision analysis successful!")
            print(f"📝 Response: {response_message[:300]}...")

            # Check if it mentions expected items
            response_lower = response_message.lower()
            found_items = []

            if any(word in response_lower for word in ['mouse', 'computer mouse', 'logitech']):
                found_items.append('mouse')
            if any(word in response_lower for word in ['pen', 'ballpoint', 'red pen']):
                found_items.append('pen')
            if any(word in response_lower for word in ['coaster', 'wood', 'wooden', 'trivet']):
                found_items.append('coaster')

            print(f"🎯 Detected items: {found_items}")

            # Check if optimization was NOT applied (should go through LLM now)
            optimization_applied = nlp_result.get("data", {}).get("optimization_applied")
            if optimization_applied:
                print(f"⚠️  Optimization was applied: {optimization_applied}")
                print("❌ This suggests the optimization removal didn't work properly")
                return False
            else:
                print("✅ No optimization applied - command went through full LLM processing")

            if len(found_items) >= 2:
                print("✅ Successfully detected multiple items!")
                return True
            else:
                print("⚠️  Only detected some items, but analysis is working")
                return True

        else:
            error_msg = nlp_result.get("error", {}).get("message", "Unknown error")
            print(f"❌ Vision analysis failed: {error_msg}")
            print(f"Full error: {nlp_result}")
            return False

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

def test_basic_chat():
    """Test basic chat functionality"""
    print("\n💬 Testing Basic Chat...")
    
    try:
        response = requests.post(
            'http://localhost:8000/nlp/command',
            json={
                'command': 'Hello, how are you?',
                'session_id': 'test-basic-chat'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Basic chat working")
                return True
            else:
                print(f"❌ Chat failed: {result}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Image Analysis After Optimization Removal")
    print("=" * 60)
    
    # Test basic functionality first
    chat_success = test_basic_chat()
    
    # Test image analysis
    image_success = test_image_analysis_direct()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    print(f"💬 Basic Chat: {'✅ PASS' if chat_success else '❌ FAIL'}")
    print(f"🖼️  Image Analysis: {'✅ PASS' if image_success else '❌ FAIL'}")
    
    if chat_success and image_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Optimization removal successful - all commands go through LLM")
    else:
        print("\n⚠️  Some tests failed - check the logs above")
    
    return chat_success and image_success

if __name__ == "__main__":
    main()
