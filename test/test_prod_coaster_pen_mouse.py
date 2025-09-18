#!/usr/bin/env python3
"""
Test production NLP with the coaster_pen_mouse.jpg image
Verify it identifies all three objects: coaster, pen, and mouse
"""

import requests
import sys
import os

BASE_URL = "http://alpine1.local:8023"
IMAGE_PATH = "test/coaster_pen_mouse.jpg"

def test_health():
    """Test server health"""
    print("🔄 Testing server health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server healthy - uptime: {data['data']['uptime_seconds']:.0f}s")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_image_analysis():
    """Test NLP image analysis with coaster_pen_mouse.jpg"""
    print(f"🔄 Testing image analysis with {IMAGE_PATH}...")
    
    # Check if image file exists
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Image file not found: {IMAGE_PATH}")
        return False
    
    print(f"✅ Image file found: {os.path.getsize(IMAGE_PATH)} bytes")
    
    try:
        # Read the image file
        with open(IMAGE_PATH, 'rb') as img_file:
            image_data = img_file.read()
        
        # Send to NLP endpoint with specific command to identify objects
        files = {'image': ('coaster_pen_mouse.jpg', image_data, 'image/jpeg')}
        data = {
            'command': 'what objects do you see in this image? please list each item you can identify',
            'session_id': 'test-coaster-pen-mouse'
        }
        
        print("📤 Sending image analysis request...")
        response = requests.post(f"{BASE_URL}/nlp/command-with-image", files=files, data=data, timeout=45)
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                response_text = result['data'].get('response', 'No response')
                analysis_text = result['data'].get('analysis', '')
                identified_items = result['data'].get('identified_items', [])

                print("✅ SUCCESS!")
                print(f"🤖 AI Response: {response_text}")
                if analysis_text:
                    print(f"🔍 Analysis: {analysis_text}")

                # Check identified_items first (more reliable)
                found_objects = []

                if identified_items:
                    print(f"\n📋 Identified Items ({len(identified_items)}):")
                    for item in identified_items:
                        name = item.get('name', '').lower()
                        description = item.get('description', '')
                        confidence = item.get('confidence', 0)
                        print(f"   • {item.get('name', 'Unknown')} (confidence: {confidence}/10)")
                        print(f"     {description}")

                        # Check for coaster
                        if 'coaster' in name:
                            found_objects.append('coaster')
                        # Check for pen
                        elif 'pen' in name:
                            found_objects.append('pen')
                        # Check for mouse
                        elif 'mouse' in name:
                            found_objects.append('mouse')

                # Fallback to text analysis if no identified_items
                if not found_objects:
                    print("\n🔍 Checking response text for objects...")
                    search_text = (response_text + ' ' + analysis_text).lower()

                    # Check for coaster
                    if any(word in search_text for word in ['coaster', 'drink coaster', 'beverage coaster']):
                        found_objects.append('coaster')

                    # Check for pen
                    if any(word in search_text for word in ['pen', 'writing pen', 'ballpoint', 'ink pen']):
                        found_objects.append('pen')

                    # Check for mouse
                    if any(word in search_text for word in ['mouse', 'computer mouse', 'wireless mouse', 'optical mouse']):
                        found_objects.append('mouse')

                # Report findings
                print(f"\n🎯 Object Detection Results:")
                if 'coaster' in found_objects:
                    print("✅ Found: COASTER")
                else:
                    print("❌ Missing: COASTER")

                if 'pen' in found_objects:
                    print("✅ Found: PEN")
                else:
                    print("❌ Missing: PEN")

                if 'mouse' in found_objects:
                    print("✅ Found: MOUSE")
                else:
                    print("❌ Missing: MOUSE")
                
                print(f"\n📊 Detection Summary: {len(found_objects)}/3 objects found")
                
                if len(found_objects) == 3:
                    print("🎉 ALL THREE OBJECTS DETECTED!")
                    return True
                elif len(found_objects) >= 2:
                    print("⚠️  Most objects detected, but not all three")
                    return False
                else:
                    print("❌ Failed to detect most objects")
                    return False
                    
            else:
                error = result.get('error', {})
                print(f"❌ FAILED: {error.get('message', 'Unknown error')}")
                print(f"Error type: {error.get('type', 'Unknown')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Raw response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>45 seconds)")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_follow_up_command():
    """Test a follow-up command to add the identified items to a bin"""
    print("\n🔄 Testing follow-up command to add items to inventory...")
    
    try:
        data = {
            'command': 'add these items to bin 10',
            'session_id': 'test-coaster-pen-mouse'  # Same session to maintain context
        }
        
        response = requests.post(f"{BASE_URL}/nlp/command", json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                response_text = result['data'].get('response', 'No response')
                print("✅ Follow-up command successful!")
                print(f"🤖 Response: {response_text[:200]}...")
                return True
            else:
                print("❌ Follow-up command failed")
                return False
        else:
            print(f"❌ Follow-up command HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Follow-up command exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Local Docker NLP Test: Coaster, Pen, Mouse Detection")
    print(f"🎯 Target: {BASE_URL}")
    print(f"🖼️  Image: {IMAGE_PATH}")
    print("="*60)
    
    # Test health first
    if not test_health():
        print("❌ Server not healthy, aborting test")
        sys.exit(1)
    
    print()
    
    # Test image analysis
    success = test_image_analysis()
    
    if success:
        # Test follow-up command
        follow_up_success = test_follow_up_command()
    
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    
    if success:
        print("🎉 Image analysis: ALL THREE OBJECTS DETECTED!")
        if 'follow_up_success' in locals() and follow_up_success:
            print("🎉 Follow-up command: SUCCESSFUL!")
            print("✅ Complete NLP image workflow is working perfectly!")
        else:
            print("⚠️  Follow-up command had issues, but main detection works")
    else:
        print("❌ Image analysis: Failed to detect all three objects")
        print("🔧 The vision system may need tuning or the objects aren't clearly visible")
    
    print("\n🏁 Test completed!")
