#!/usr/bin/env python3
"""
Test script to demonstrate the new centralized logging for current_bin debugging
This script will make API calls and show detailed logging of current_bin updates
"""

import requests
import sys
import os

# Add the project root to the path so we can import modules
sys.path.append('.')

from utils.logging import setup_logger, set_global_log_level

def main():
    """Test current_bin logging with various scenarios"""
    
    # Set up logging for this test script
    logger = setup_logger(__name__)
    
    print("🧪 Testing Current Bin Logging")
    print("=" * 50)
    
    # Set log level to INFO to see all the current_bin tracking
    set_global_log_level("INFO")
    
    base_url = 'http://localhost:8001'
    
    # Test scenarios that should trigger different current_bin behaviors
    test_scenarios = [
        ("add a hammer to bin A", "Should set current_bin to 'A'"),
        ("what's in bin A", "Should set current_bin to 'A' (get_bin_contents)"),
        ("search for tools", "Should NOT change current_bin (search_items)"),
        ("add a screwdriver to bin B", "Should set current_bin to 'B'"),
        ("move the hammer to bin C", "Should set current_bin to 'C'"),
        ("what's in my toolbox", "Depends on LLM function choice - search vs get_bin_contents"),
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
            current_bin = chat_data.get('current_bin')
            
            print(f"   📤 Response: '{chat_data['response'][:60]}...'")
            print(f"   📦 Returned current_bin: '{current_bin}'")
            
            # Brief pause to make logs easier to read
            import time
            time.sleep(1)
        
        print(f"\n✅ Test completed! Check the server logs above to see detailed current_bin tracking.")
        print(f"🔍 Look for log entries like:")
        print(f"   - CHAT_REQUEST: Shows incoming message and current_bin_before")
        print(f"   - SET_CURRENT_BIN: Shows when and how current_bin changes")
        print(f"   - CHAT_RESPONSE: Shows final current_bin being returned")
        
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
        print(f"💡 Make sure BinBot server is running on {base_url}")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    main()
