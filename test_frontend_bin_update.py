#!/usr/bin/env python3
"""
Test script to simulate frontend bin update behavior
"""

import requests
import json

def test_bin_update_flow():
    """Test the complete bin update flow"""
    base_url = 'http://localhost:8001'
    
    print("🧪 Testing Frontend Bin Update Flow")
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
    
    # Step 2: Send first chat message to add item to bin A
    print("\n2️⃣ Adding item to bin A...")
    chat_payload = {'message': 'add a screwdriver to bin A'}
    chat_resp = requests.post(f'{base_url}/api/chat/command', json=chat_payload, cookies=cookies)
    
    if not chat_resp.ok:
        print(f"❌ Chat request failed: {chat_resp.status_code}")
        return
    
    chat_data = chat_resp.json()
    print(f"✅ Chat response: {chat_data['response'][:50]}...")
    print(f"📦 Current bin from response: {chat_data.get('current_bin')}")
    
    # Simulate frontend logic
    frontend_current_bin = None  # Initial state
    server_current_bin = chat_data.get('current_bin')
    
    print(f"🔍 Frontend bin: {frontend_current_bin}, Server bin: {server_current_bin}")
    
    if server_current_bin and server_current_bin != frontend_current_bin:
        print(f"🎯 Bin change detected: {frontend_current_bin} → {server_current_bin}")
        frontend_current_bin = server_current_bin
        
        # Get bin contents
        bin_resp = requests.get(f'{base_url}/api/inventory/bin/{server_current_bin}', cookies=cookies)
        if bin_resp.ok:
            bin_data = bin_resp.json()
            print(f"📋 Bin {server_current_bin} contents: {len(bin_data['items'])} items")
        else:
            print(f"❌ Failed to get bin contents: {bin_resp.status_code}")
    
    # Step 3: Send second chat message to add item to bin B
    print("\n3️⃣ Adding item to bin B...")
    chat_payload = {'message': 'add a hammer to bin B'}
    chat_resp = requests.post(f'{base_url}/api/chat/command', json=chat_payload, cookies=cookies)
    
    if not chat_resp.ok:
        print(f"❌ Chat request failed: {chat_resp.status_code}")
        return
    
    chat_data = chat_resp.json()
    print(f"✅ Chat response: {chat_data['response'][:50]}...")
    print(f"📦 Current bin from response: {chat_data.get('current_bin')}")
    
    # Simulate frontend logic for bin change
    server_current_bin = chat_data.get('current_bin')
    
    print(f"🔍 Frontend bin: {frontend_current_bin}, Server bin: {server_current_bin}")
    
    if server_current_bin and server_current_bin != frontend_current_bin:
        print(f"🎯 Bin change detected: {frontend_current_bin} → {server_current_bin}")
        frontend_current_bin = server_current_bin
        
        # Get bin contents
        bin_resp = requests.get(f'{base_url}/api/inventory/bin/{server_current_bin}', cookies=cookies)
        if bin_resp.ok:
            bin_data = bin_resp.json()
            print(f"📋 Bin {server_current_bin} contents: {len(bin_data['items'])} items")
            for item in bin_data['items']:
                print(f"   - {item['name']}")
        else:
            print(f"❌ Failed to get bin contents: {bin_resp.status_code}")
    elif server_current_bin:
        print(f"🔄 Same bin, refreshing contents: {server_current_bin}")
        # Get bin contents
        bin_resp = requests.get(f'{base_url}/api/inventory/bin/{server_current_bin}', cookies=cookies)
        if bin_resp.ok:
            bin_data = bin_resp.json()
            print(f"📋 Bin {server_current_bin} contents: {len(bin_data['items'])} items")
    
    # Step 4: Add another item to the same bin
    print("\n4️⃣ Adding another item to same bin...")
    chat_payload = {'message': 'add a nail to the current bin'}
    chat_resp = requests.post(f'{base_url}/api/chat/command', json=chat_payload, cookies=cookies)
    
    if not chat_resp.ok:
        print(f"❌ Chat request failed: {chat_resp.status_code}")
        return
    
    chat_data = chat_resp.json()
    print(f"✅ Chat response: {chat_data['response'][:50]}...")
    print(f"📦 Current bin from response: {chat_data.get('current_bin')}")
    
    # Simulate frontend logic
    server_current_bin = chat_data.get('current_bin')
    
    print(f"🔍 Frontend bin: {frontend_current_bin}, Server bin: {server_current_bin}")
    
    if server_current_bin and server_current_bin != frontend_current_bin:
        print(f"🎯 Bin change detected: {frontend_current_bin} → {server_current_bin}")
        frontend_current_bin = server_current_bin
    elif server_current_bin:
        print(f"🔄 Same bin, should refresh contents: {server_current_bin}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_bin_update_flow()
