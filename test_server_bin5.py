#!/usr/bin/env python3
"""
Simple test to check what's in bin 5 via the server API
"""

import requests
import json
import time

def test_health():
    """Test server health"""
    print("🔄 Testing server health...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Server is healthy!")
            print(f"   Status: {data.get('status')}")
            
            services = data.get('services', {})
            for service, status in services.items():
                print(f"   {service}: {status}")
            
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_bin5_query():
    """Test querying what's in bin 5"""
    print("\n🔄 Testing 'what is in bin 5?' query...")
    
    try:
        url = "http://localhost:8000/nlp/command"
        payload = {
            "command": "what is in bin 5?",
            "session_id": "test-session-bin5"
        }
        
        print(f"📤 Sending: {payload['command']}")
        
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Query successful!")
            
            # Pretty print the response
            print("\n📋 Full Response:")
            print(json.dumps(data, indent=2))
            
            if data.get('success'):
                response_data = data.get('data', {})
                message = response_data.get('response', 'No response message')
                print(f"\n💬 Bot Response: {message}")
                
                return True
            else:
                error = data.get('error', {})
                print(f"\n❌ Query failed: {error}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Query error: {e}")
        return False

def test_simple_query():
    """Test a simple query first"""
    print("\n🔄 Testing simple query...")
    
    try:
        url = "http://localhost:8000/nlp/command"
        payload = {
            "command": "hello, are you working?",
            "session_id": "test-session-simple"
        }
        
        print(f"📤 Sending: {payload['command']}")
        
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Simple query successful!")
            
            if data.get('success'):
                response_data = data.get('data', {})
                message = response_data.get('response', 'No response message')
                print(f"💬 Bot Response: {message}")
                return True
            else:
                error = data.get('error', {})
                print(f"❌ Simple query failed: {error}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Simple query error: {e}")
        return False

def main():
    """Run the tests"""
    print("🚀 Testing Bin 5 Query via Server API")
    print("=" * 50)
    
    # Test health first
    if not test_health():
        print("\n❌ Server health check failed. Is the server running?")
        print("💡 Try: docker-compose --env-file .env up --build")
        return False
    
    # Test simple query
    if not test_simple_query():
        print("\n❌ Simple query failed. Check server logs.")
        return False
    
    # Test bin 5 query
    if test_bin5_query():
        print("\n🎉 Bin 5 query test completed successfully!")
        print("✅ The refactored LLM integration is working with the server!")
    else:
        print("\n⚠️  Bin 5 query failed. This might be expected if bin 5 is empty.")
        print("💡 Try adding some items to bin 5 first, then query again.")
    
    return True

if __name__ == "__main__":
    main()
