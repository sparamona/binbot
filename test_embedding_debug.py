#!/usr/bin/env python3
"""
Debug embedding generation issue
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_embedding_debug():
    """Test the embedding debug endpoint"""
    print("🔄 Testing embedding debug endpoint...")
    
    try:
        response = requests.post(f"{BASE_URL}/test/debug-embedding", 
                               json={"text": "Red Box"}, 
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Embedding generation successful!")
                print(f"Text: {result['data']['text']}")
                print(f"Embedding stats: {json.dumps(result['data']['embedding_stats'], indent=2)}")
                return True
            else:
                print("❌ Embedding generation failed")
                print(f"Error: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_simple_add():
    """Test simple add endpoint directly"""
    print("\n🔄 Testing simple add endpoint...")
    
    try:
        response = requests.post(f"{BASE_URL}/add", 
                               json={"items": ["Red Box"], "bin_id": "99"}, 
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Add response: {json.dumps(result, indent=2)}")
            return result.get('success', False)
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🧪 Embedding Debug Test")
    print("="*50)
    
    # Test 1: Direct embedding debug
    test_embedding_debug()
    
    # Test 2: Simple add endpoint
    test_simple_add()
    
    print("\n🏁 Debug test completed!")

if __name__ == "__main__":
    main()
