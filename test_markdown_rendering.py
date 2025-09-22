#!/usr/bin/env python3
"""
Test script to verify markdown rendering in BinBot chat responses
This script will send test messages that should trigger markdown-formatted responses
"""

import requests
import sys

def main():
    """Test markdown rendering with various scenarios"""
    
    print("🎨 Testing Markdown Rendering in BinBot")
    print("=" * 50)
    
    base_url = 'http://localhost:8001'
    
    # Test scenarios that should show different markdown formatting
    test_scenarios = [
        ("add a **hammer** and `screwdriver` to bin A", "Should show bold hammer and code-formatted screwdriver"),
        ("what's in bin A", "Should show formatted list of items with proper markdown"),
        ("tell me about the inventory system", "Should show formatted explanation with headers and lists"),
        ("add multiple items: hammer, screwdriver, wrench to bin B", "Should show formatted confirmation"),
    ]
    
    try:
        # Step 1: Create a new session
        print("\n1️⃣ Creating new session...")
        session_resp = requests.post(f'{base_url}/api/session')
        
        if not session_resp.ok:
            print(f"❌ Failed to create session: {session_resp.status_code}")
            return
        
        # Extract session cookie
        cookies = session_resp.cookies
        session_data = session_resp.json()
        print(f"✅ Session created: {session_data['session_id'][:8]}...")
        
        # Step 2: Run test scenarios
        for i, (message, description) in enumerate(test_scenarios, 1):
            print(f"\n{i+1}️⃣ Test: '{message}'")
            print(f"   Expected: {description}")
            
            # Send chat message
            chat_payload = {'message': message}
            chat_resp = requests.post(f'{base_url}/api/chat/command', json=chat_payload, cookies=cookies)
            
            if not chat_resp.ok:
                print(f"   ❌ Chat request failed: {chat_resp.status_code}")
                continue
            
            chat_data = chat_resp.json()
            response = chat_data['response']
            
            print(f"   📤 Raw Response:")
            print(f"   {response}")
            print(f"   📦 Current bin: '{chat_data.get('current_bin')}'")
            
            # Brief pause to make output easier to read
            import time
            time.sleep(1)
        
        print(f"\n✅ Test completed!")
        print(f"🎨 Open BinBot in your browser to see the markdown rendering:")
        print(f"   {base_url}")
        print(f"🔍 Look for:")
        print(f"   - **Bold text** for important information")
        print(f"   - `Code formatting` for item names and IDs")
        print(f"   - Bullet points for item lists")
        print(f"   - Headers (##) for organized responses")
        print(f"   - Tables for multiple items with details")
        
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
        print(f"💡 Make sure BinBot server is running on {base_url}")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    main()
