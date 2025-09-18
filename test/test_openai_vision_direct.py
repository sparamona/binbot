#!/usr/bin/env python3
"""
Direct test of OpenAI Vision API to isolate the issue
"""

import os
import base64
import requests
from PIL import Image, ImageDraw
import io
import json

def create_test_image():
    """Create a simple test image"""
    img = Image.new('RGB', (200, 200), 'white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 150, 150], fill='red', outline='black', width=2)
    draw.text((75, 160), "Red Box", fill='black')
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=90)
    img_bytes.seek(0)
    
    return img_bytes.getvalue()

def encode_image(image_data):
    """Encode image to base64"""
    return base64.b64encode(image_data).decode('utf-8')

def test_vision_api_direct():
    """Test OpenAI Vision API directly"""
    
    # Get API key
    api_key = None
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    break
    except FileNotFoundError:
        pass
    
    if not api_key:
        api_key = os.environ.get('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ No OpenAI API key found")
        return False
    
    print(f"🔑 Using API key: {api_key[:10]}...{api_key[-4:]}")
    
    # Create test image
    print("🖼️ Creating test image...")
    image_data = create_test_image()
    base64_image = encode_image(image_data)
    print(f"✅ Image created and encoded ({len(base64_image)} chars)")
    
    # Prepare the request
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What do you see in this image? Please describe it briefly."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300,
        "temperature": 0.1
    }
    
    print("\n🔄 Testing Vision API...")
    print(f"Model: {payload['model']}")
    print(f"Max tokens: {payload['max_tokens']}")
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print("✅ Vision API working!")
            print(f"Response: {content}")
            return True
            
        elif response.status_code == 429:
            print("❌ Rate limit exceeded (429)")
            try:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'No details')
                print(f"Error: {error_msg}")
                
                # Check if it's quota or rate limit
                if 'quota' in error_msg.lower():
                    print("🚨 This is a QUOTA issue - you need to add credits")
                elif 'rate' in error_msg.lower():
                    print("⏰ This is a RATE LIMIT issue - try again in a moment")
                else:
                    print("❓ Unknown 429 error type")
                    
            except:
                print(f"Raw response: {response.text}")
            return False
            
        elif response.status_code == 400:
            print("❌ Bad request (400)")
            try:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'No details')
                print(f"Error: {error_msg}")
                
                # Check if it's a model issue
                if 'model' in error_msg.lower():
                    print("🔄 Trying with gpt-4o model instead...")
                    return test_with_different_model(headers, base64_image)
                    
            except:
                print(f"Raw response: {response.text}")
            return False
            
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False

def test_with_different_model(headers, base64_image):
    """Try with a different model"""
    
    payload = {
        "model": "gpt-4o",  # Try the newer model
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What do you see in this image? Please describe it briefly."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"gpt-4o Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print("✅ gpt-4o Vision API working!")
            print(f"Response: {content}")
            print("\n💡 Solution: Update your config to use 'gpt-4o' instead of 'gpt-4-vision-preview'")
            return True
        else:
            print(f"❌ gpt-4o also failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ gpt-4o test failed: {e}")
        return False

def main():
    print("🚀 Direct OpenAI Vision API Test")
    print("="*50)
    
    success = test_vision_api_direct()
    
    if not success:
        print("\n" + "="*50)
        print("🔧 TROUBLESHOOTING SUGGESTIONS")
        print("="*50)
        print("1. Check your OpenAI billing dashboard")
        print("2. Verify you have vision API access")
        print("3. Try waiting a few minutes for rate limits to reset")
        print("4. Consider switching to Gemini as alternative")

if __name__ == "__main__":
    main()
