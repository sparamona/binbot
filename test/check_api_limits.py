#!/usr/bin/env python3
"""
Simple script to test API access and understand the 429 error
"""

import os
import requests
import json
from datetime import datetime

def get_api_key():
    """Get API key from .env file"""
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    return line.split('=', 1)[1].strip()
    except FileNotFoundError:
        pass
    return os.environ.get('OPENAI_API_KEY')

def test_simple_completion(api_key):
    """Test a simple completion to see the exact error"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Very simple, minimal request
    payload = {
        "model": "gpt-3.5-turbo",  # Try cheaper model first
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 5
    }
    
    print("🔄 Testing simple completion with gpt-3.5-turbo...")
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API is working!")
            print(f"Response: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"❌ Error {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
                
                # Parse the specific error
                error = error_data.get('error', {})
                error_type = error.get('type', '')
                error_code = error.get('code', '')
                error_message = error.get('message', '')
                
                print(f"\n📋 Error Analysis:")
                print(f"   Type: {error_type}")
                print(f"   Code: {error_code}")
                print(f"   Message: {error_message}")
                
                if error_type == 'insufficient_quota':
                    print(f"\n💡 DIAGNOSIS: Your API key has exceeded its quota")
                    print(f"   This means you've used up all available credits")
                    print(f"   You need to add more credits to your OpenAI account")
                elif error_code == 'rate_limit_exceeded':
                    print(f"\n💡 DIAGNOSIS: Rate limit exceeded")
                    print(f"   Try again in a few minutes")
                else:
                    print(f"\n❓ DIAGNOSIS: Unknown error type")
                    
            except:
                print(f"Raw response: {response.text}")
            
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_models_endpoint(api_key):
    """Test the models endpoint to verify API key works"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print("\n🔄 Testing models endpoint...")
    
    try:
        response = requests.get('https://api.openai.com/v1/models', headers=headers, timeout=10)
        print(f"Models endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            models = response.json()
            model_count = len(models.get('data', []))
            print(f"✅ API key is valid - {model_count} models available")
            
            # Check if vision models are available
            vision_models = [m for m in models.get('data', []) if 'vision' in m.get('id', '').lower() or 'gpt-4o' in m.get('id', '')]
            if vision_models:
                print(f"✅ Vision models available: {len(vision_models)}")
                for model in vision_models[:3]:  # Show first 3
                    print(f"   - {model.get('id')}")
            else:
                print(f"❌ No vision models found")
                
            return True
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Models endpoint error: {e}")
        return False

def main():
    print("🚀 OpenAI API Limits and Error Checker")
    print("="*50)
    
    api_key = get_api_key()
    if not api_key:
        print("❌ No OpenAI API key found")
        return
    
    print(f"🔑 API Key: {api_key[:10]}...{api_key[-4:]}")
    
    # Test models endpoint first
    models_ok = test_models_endpoint(api_key)
    
    if models_ok:
        # Test actual completion
        completion_ok = test_simple_completion(api_key)
        
        print("\n" + "="*50)
        print("📊 SUMMARY")
        print("="*50)
        
        if completion_ok:
            print("✅ Your API key is working perfectly!")
            print("   The 429 error in your app might be temporary")
        else:
            print("❌ Your API key has quota/billing issues")
            print("\n🔧 SOLUTIONS:")
            print("1. 💳 Add credits: https://platform.openai.com/account/billing")
            print("2. 🔑 Try a different API key")
            print("3. 🔄 Switch to Gemini (free alternative)")
            print("4. ⏰ Wait if it's a rate limit (resets hourly/daily)")
            
            print("\n📱 To add credits:")
            print("   • Go to https://platform.openai.com/account/billing")
            print("   • Click 'Add to credit balance'")
            print("   • Add $5-10 to get started")
            print("   • Credits are used as you make API calls")
    else:
        print("❌ API key has fundamental issues")
        print("   Check if the key is correct and not expired")

if __name__ == "__main__":
    main()
