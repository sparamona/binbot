#!/usr/bin/env python3
import requests
from PIL import Image, ImageDraw
import io

# Create a simple test image
img = Image.new('RGB', (200, 200), color='white')
draw = ImageDraw.Draw(img)
draw.rectangle([50, 50, 150, 100], fill='red', outline='black')
draw.text((60, 65), 'Hammer', fill='black')

img_bytes = io.BytesIO()
img.save(img_bytes, format='JPEG')
img_bytes.seek(0)

print("Testing /upload-image endpoint...")

files = {'image': ('test.jpg', img_bytes, 'image/jpeg')}
data = {'command': 'add these items to bin 9', 'session_id': 'simple-test'}

response = requests.post('http://localhost:8000/nlp/upload-image', files=files, data=data, timeout=60)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Success: {result.get('success')}")
    print(f"📄 Response: {result.get('data', {}).get('response', 'No response')}")
else:
    print(f"❌ Error {response.status_code}: {response.text}")
