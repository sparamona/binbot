#!/usr/bin/env python3
"""
Test script to reproduce the NoneType error that occurs after image-based item creation
"""

import requests
import time
import json

def test_reproduce_error():
    """Reproduce the exact error scenario described by the user"""
    
    session_id = 'reproduce-error-test'
    base_url = 'http://localhost:8000'
    
    print('🧪 Reproducing the NoneType error scenario...')
    print(f'Session ID: {session_id}')
    
    try:
        # Step 1: Upload photo and analyze
        print('\n1. Upload photo')
        with open('coaster_pen_mouse.jpg', 'rb') as f:
            files = {'image': ('test.jpg', f, 'image/jpeg')}
            data = {'command': 'What items can you see?', 'session_id': session_id}
            r = requests.post(f'{base_url}/nlp/command-with-image', files=files, data=data, timeout=30)
        
        result = r.json()
        print(f'   Status: {r.status_code}, Success: {result.get("success", False)}')
        if not result.get('success'):
            print(f'   Error: {result.get("error", {}).get("message", "Unknown")}')
            return False

        # Step 2: Add all these items to bin 13
        print('\n2. Add all these items to bin 13')
        with open('coaster_pen_mouse.jpg', 'rb') as f:
            files = {'image': ('test.jpg', f, 'image/jpeg')}
            data = {'command': 'add all these items to bin 13', 'session_id': session_id}
            r = requests.post(f'{base_url}/nlp/command-with-image', files=files, data=data, timeout=30)
        
        result = r.json()
        print(f'   Status: {r.status_code}, Success: {result.get("success", False)}')
        if not result.get('success'):
            print(f'   Error: {result.get("error", {}).get("message", "Unknown")}')
            return False

        # Step 3: Add a fork to bin 13 (no image)
        print('\n3. Add a fork to bin 13')
        r = requests.post(f'{base_url}/nlp/command', 
                         json={'command': 'add a fork to bin 13', 'session_id': session_id}, 
                         timeout=15)
        result = r.json()
        print(f'   Status: {r.status_code}, Success: {result.get("success", False)}')
        if not result.get('success'):
            print(f'   Error: {result.get("error", {}).get("message", "Unknown")}')
            return False

        # Step 4: Add a spoon to bin 13 (no image) - This should trigger the error
        print('\n4. Add a spoon to bin 13 (This was causing the error)')
        r = requests.post(f'{base_url}/nlp/command', 
                         json={'command': 'add a spoon to bin 13', 'session_id': session_id}, 
                         timeout=15)
        result = r.json()
        print(f'   Status: {r.status_code}, Success: {result.get("success", False)}')
        if not result.get('success'):
            print(f'   ❌ ERROR REPRODUCED: {result.get("error", {}).get("message", "Unknown")}')
            print(f'   Full error details: {json.dumps(result.get("error", {}), indent=2)}')
            return False
        else:
            print('   ✅ SUCCESS: No error! The issue is fixed!')
            print(f'   Response: {result.get("data", {}).get("message", "No message")}')
            return True

    except Exception as e:
        print(f'❌ Exception occurred: {e}')
        return False

if __name__ == '__main__':
    success = test_reproduce_error()
    if success:
        print('\n🎉 Test passed! The error has been fixed.')
    else:
        print('\n💥 Test failed! The error still exists.')
