#!/usr/bin/env python3
"""
Test script for the /api/chat/image endpoint
"""

import requests
import json
from pathlib import Path

def test_image_endpoint():
    """Test the image upload endpoint"""
    
    # API endpoint
    url = "http://localhost:8000/api/chat/image"
    
    # Test image path
    image_path = Path("test/coaster_pen_mouse.jpg")
    
    if not image_path.exists():
        print(f"Error: Test image not found at {image_path}")
        return
    
    print(f"Testing image upload endpoint with: {image_path}")
    print(f"URL: {url}")
    
    # First, create a session to get session_id cookie
    session_url = "http://localhost:8000/api/session"
    print(f"\nCreating session at: {session_url}")
    
    try:
        session_response = requests.post(session_url)
        print(f"Session response status: {session_response.status_code}")
        print(f"Session response: {session_response.text}")
        
        if session_response.status_code != 200:
            print("Failed to create session")
            return
            
        # Get session cookie and session_id from response
        session_cookies = session_response.cookies
        session_data = session_response.json()
        session_id = session_data.get('session_id')
        print(f"Session cookies: {dict(session_cookies)}")
        print(f"Session ID: {session_id}")

    except Exception as e:
        print(f"Error creating session: {e}")
        return

    # Now test the image upload
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (image_path.name, f, 'image/jpeg')}

            print(f"\nUploading image...")
            # Try with both cookies and manual session_id cookie
            manual_cookies = {'session_id': session_id}
            response = requests.post(url, files=files, cookies=manual_cookies)
            
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Raw response text: {response.text}")

            if response.status_code == 200:
                try:
                    json_response = response.json()
                    print(f"\nParsed JSON response:")
                    print(json.dumps(json_response, indent=2))
                except json.JSONDecodeError:
                    print("Response is not valid JSON")
            elif response.status_code == 500:
                print(f"Internal server error occurred")
                # Try to get more details by checking if it's JSON
                try:
                    error_json = response.json()
                    print(f"Error details: {json.dumps(error_json, indent=2)}")
                except:
                    print("No JSON error details available")
            else:
                print(f"Request failed with status {response.status_code}")
                
    except Exception as e:
        print(f"Error uploading image: {e}")

if __name__ == "__main__":
    test_image_endpoint()
