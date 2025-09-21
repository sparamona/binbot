#!/usr/bin/env python3
"""
Test script to verify current_bin updates are working correctly
"""

import requests
import json

def test_current_bin_updates():
    """Test that current_bin updates work correctly"""
    base_url = 'http://localhost:8001'
    
    print("🧪 Testing Current Bin Updates")
    print("=" * 50)
    
    # Step 1: Create session
    print("\n1️⃣ Creating session...")
    session_resp = requests.post(f'{base_url}/api/session')
    if not session_resp.ok:
        print(f"❌ Session creation failed: {session_resp.status_code}")
        return
    
    session_data = session_resp.json()
    cookies = session_resp.cookies
    print(f"✅ Session created: {session_data['session_id'][:8]}...")
    
    # Test sequence: Add items to different bins and verify current_bin updates
    test_cases = [
        ("add a screwdriver to bin ALPHA", "ALPHA"),
        ("add a hammer to bin BETA", "BETA"),
        ("add a nail to bin GAMMA", "GAMMA"),
        ("add another screwdriver to the current bin", "GAMMA"),  # Should stay in GAMMA
        ("add a wrench to bin DELTA", "DELTA"),
    ]
    
    current_frontend_bin = None
    
    for i, (message, expected_bin) in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ Test: '{message}'")
        print(f"   Expected bin: {expected_bin}")
        
        # Send chat message
        chat_payload = {'message': message}
        chat_resp = requests.post(f'{base_url}/api/chat/command', json=chat_payload, cookies=cookies)
        
        if not chat_resp.ok:
            print(f"   ❌ Chat request failed: {chat_resp.status_code}")
            continue
        
        chat_data = chat_resp.json()
        server_current_bin = chat_data.get('current_bin')
        
        print(f"   📤 Server response: '{chat_data['response'][:40]}...'")
        print(f"   📦 Server current_bin: {server_current_bin}")
        print(f"   🔍 Frontend current_bin: {current_frontend_bin}")
        
        # Simulate frontend logic
        if server_current_bin:
            if server_current_bin != current_frontend_bin:
                print(f"   🎯 BIN CHANGE DETECTED: {current_frontend_bin} → {server_current_bin}")
                current_frontend_bin = server_current_bin
                
                # Verify bin contents
                bin_resp = requests.get(f'{base_url}/api/inventory/bin/{server_current_bin}', cookies=cookies)
                if bin_resp.ok:
                    bin_data = bin_resp.json()
                    print(f"   📋 Bin {server_current_bin} now has {len(bin_data['items'])} items")
                    for item in bin_data['items']:
                        print(f"      - {item['name']}")
                else:
                    print(f"   ❌ Failed to get bin contents: {bin_resp.status_code}")
            else:
                print(f"   🔄 Same bin, contents refreshed: {server_current_bin}")
        else:
            print(f"   ⚠️ No current_bin in response")
        
        # Verify expectation
        if server_current_bin == expected_bin:
            print(f"   ✅ PASS: Current bin matches expected ({expected_bin})")
        else:
            print(f"   ❌ FAIL: Expected {expected_bin}, got {server_current_bin}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print(f"   Final frontend bin: {current_frontend_bin}")
    print("   All bin changes should have been detected and handled correctly")
    print("✅ Test completed!")

if __name__ == "__main__":
    test_current_bin_updates()
