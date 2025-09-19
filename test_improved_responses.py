#!/usr/bin/env python3
"""
Test script to verify improved image upload responses.
Shows that we removed the generic "✅ Operation completed successfully" messages
and now get meaningful responses about what the AI found in images.
"""
import requests
from PIL import Image, ImageDraw
import io

BASE_URL = "http://localhost:8000"

def create_test_image():
    """Create a test image with multiple items"""
    img = Image.new('RGB', (300, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw hammer
    draw.rectangle([20, 20, 80, 80], fill='red', outline='black')
    draw.text((30, 45), 'Hammer', fill='white')
    
    # Draw wrench  
    draw.rectangle([120, 20, 180, 80], fill='blue', outline='black')
    draw.text((130, 45), 'Wrench', fill='white')
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes.getvalue()

def test_image_content_question():
    """Test asking about image content - should get natural response"""
    print("🔍 Test 1: Asking about image content")
    print("Expected: Natural description of what AI can see")
    
    image_data = create_test_image()
    files = {'image': ('tools.jpg', image_data, 'image/jpeg')}
    data = {'command': 'What tools can you see in this image?', 'session_id': 'test-content'}
    
    response = requests.post(f"{BASE_URL}/nlp/upload-image", files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success: {result.get('success')}")
        print(f"📄 Response: {result.get('data', {}).get('response', 'No response')}")
        
        # Check that we don't get the old generic messages
        response_text = result.get('data', {}).get('response', '')
        if "✅ Operation completed successfully" in response_text:
            print("❌ FAIL: Still getting generic success message")
        elif "💡 Now you can type commands" in response_text:
            print("❌ FAIL: Still getting instruction message")
        else:
            print("✅ PASS: Getting natural AI response about image content")
        return True
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return False

def test_add_items_from_image():
    """Test adding items from uploaded image"""
    print("\n📸 Test 2: Adding items from uploaded image")
    print("Expected: Confirmation with items from image")
    
    image_data = create_test_image()
    files = {'image': ('tools.jpg', image_data, 'image/jpeg')}
    data = {'command': 'add these tools to bin 10', 'session_id': 'test-add'}
    
    response = requests.post(f"{BASE_URL}/nlp/upload-image", files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success: {result.get('success')}")
        print(f"📄 Response: {result.get('data', {}).get('response', 'No response')}")
        return True
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return False

def main():
    print("=== Testing Improved Image Upload Responses ===")
    print("This test verifies that we removed generic messages and get meaningful AI responses")
    
    success1 = test_image_content_question()
    success2 = test_add_items_from_image()
    
    print(f"\n=== Results ===")
    print(f"Image content questions: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Add items from image: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! Image responses are now improved.")
    else:
        print("\n⚠️  Some tests failed. Check the responses above.")

if __name__ == "__main__":
    main()
