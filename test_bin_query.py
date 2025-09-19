#!/usr/bin/env python3
"""
Test script to check what's in bin 5 using the refactored LLM integration
"""

import os
import sys
import asyncio
import requests
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_env_file():
    """Load environment variables from .env file"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print(f"⚠️  No .env file found at {env_path}")

def wait_for_server(url="http://localhost:8000/health", timeout=30):
    """Wait for the server to be ready"""
    print(f"🔄 Waiting for server at {url}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(2)
    
    print(f"❌ Server not ready after {timeout} seconds")
    return False

def test_health_endpoint():
    """Test the health endpoint"""
    print("\n🔄 Testing health endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health endpoint working")
            print(f"   Status: {data.get('status')}")
            print(f"   Services: {data.get('services', {})}")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_bin_query():
    """Test querying what's in bin 5"""
    print("\n🔄 Testing bin 5 query...")
    
    try:
        # Test the NLP command endpoint
        url = "http://localhost:8000/nlp/command"
        payload = {
            "command": "what is in bin 5?",
            "session_id": "test-bin-query-session"
        }
        
        print(f"📤 Sending request: {payload['command']}")
        
        response = requests.post(
            url, 
            json=payload, 
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Bin query successful!")
            
            if data.get('success'):
                response_data = data.get('data', {})
                message = response_data.get('response', 'No response message')
                print(f"📋 Response: {message}")
                
                # Check if there are any items
                items = response_data.get('items', [])
                if items:
                    print(f"📦 Found {len(items)} items in bin 5:")
                    for i, item in enumerate(items, 1):
                        print(f"   {i}. {item.get('name', 'Unknown')} - {item.get('description', 'No description')}")
                else:
                    print("📭 Bin 5 appears to be empty or no items found")
                
                return True
            else:
                error = data.get('error', {})
                print(f"❌ Query failed: {error.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Bin query error: {e}")
        return False

def test_with_direct_llm():
    """Test the LLM integration directly without server"""
    print("\n🔄 Testing direct LLM integration...")
    
    try:
        # Load environment variables
        load_env_file()
        
        from llm.client import LLMClient
        from config.settings import Settings
        
        # Initialize settings and client
        settings = Settings()
        llm_client = LLMClient(settings.config)
        
        if not llm_client.initialize():
            print("❌ Could not initialize LLM client")
            return False
        
        print(f"✅ LLM client initialized with provider: {llm_client.provider_name}")
        
        # Test a simple chat completion
        messages = [
            {"role": "system", "content": "You are a helpful assistant for an inventory management system."},
            {"role": "user", "content": "I want to know what items are stored in bin 5. How would you help me find this information?"}
        ]
        
        response = asyncio.run(llm_client.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=200
        ))
        
        if response and response.content:
            print("✅ Direct LLM test successful!")
            print(f"📝 LLM Response: {response.content}")
            return True
        else:
            print("❌ Direct LLM test failed - no response")
            return False
            
    except Exception as e:
        print(f"❌ Direct LLM test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the bin 5 query test"""
    print("🚀 Testing Bin 5 Query with Refactored LLM")
    print("=" * 50)
    
    # First try direct LLM test (doesn't require server)
    direct_test_result = test_with_direct_llm()
    
    if not direct_test_result:
        print("\n❌ Direct LLM test failed. Check your API keys and configuration.")
        return False
    
    # Try to test with server if it's running
    print("\n" + "=" * 50)
    print("🌐 Testing with Server")
    print("=" * 50)
    
    if wait_for_server():
        health_result = test_health_endpoint()
        if health_result:
            bin_query_result = test_bin_query()
            
            if bin_query_result:
                print("\n🎉 All tests passed! The refactored LLM integration is working correctly.")
            else:
                print("\n⚠️  Server is running but bin query failed. Check the logs.")
        else:
            print("\n⚠️  Server is running but health check failed.")
    else:
        print("\n💡 Server not running. To test with full functionality:")
        print("   1. Run: docker-compose --env-file .env up --build")
        print("   2. Wait for server to start")
        print("   3. Run this test again")
    
    return True

if __name__ == "__main__":
    main()
