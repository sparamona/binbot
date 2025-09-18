#!/usr/bin/env python3
"""
Script to check OpenAI API key status and quota
"""

import os
import requests
from datetime import datetime

def check_openai_status():
    """Check OpenAI API key status and quota"""
    
    # Get API key from environment or .env file
    api_key = None
    
    # Try to read from .env file
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    break
    except FileNotFoundError:
        pass
    
    # Fallback to environment variable
    if not api_key:
        api_key = os.environ.get('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ No OpenAI API key found")
        return False
    
    print(f"🔑 API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Test API key with a simple request
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Try to list models (this is a lightweight request)
    print("\n🔄 Testing API key with models endpoint...")
    try:
        response = requests.get('https://api.openai.com/v1/models', headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API key is valid and working")
            models = response.json()
            print(f"Available models: {len(models.get('data', []))}")
            return True
        elif response.status_code == 401:
            print("❌ API key is invalid or expired")
            print(f"Response: {response.text}")
            return False
        elif response.status_code == 429:
            print("❌ Rate limit or quota exceeded")
            print(f"Response: {response.text}")
            
            # Try to get more details from the error
            try:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'No details')
                print(f"Error details: {error_msg}")
            except:
                pass
            return False
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False

def suggest_solutions():
    """Suggest solutions for quota issues"""
    print("\n" + "="*60)
    print("💡 SOLUTIONS FOR OPENAI QUOTA ISSUES")
    print("="*60)
    
    print("\n1. 🔄 ADD CREDITS TO YOUR OPENAI ACCOUNT:")
    print("   - Go to https://platform.openai.com/account/billing")
    print("   - Add a payment method and credits")
    print("   - Check your usage limits")
    
    print("\n2. 🆕 GET A NEW API KEY:")
    print("   - Go to https://platform.openai.com/api-keys")
    print("   - Create a new API key")
    print("   - Update your .env file with the new key")
    
    print("\n3. 🔄 SWITCH TO GEMINI (FREE ALTERNATIVE):")
    print("   - Get a free Gemini API key from https://makersuite.google.com/app/apikey")
    print("   - Add it to your .env file as GEMINI_API_KEY=your-key-here")
    print("   - Change config.yaml: llm.provider from 'openai' to 'gemini'")
    
    print("\n4. ⏰ WAIT FOR QUOTA RESET:")
    print("   - OpenAI quotas reset monthly")
    print("   - Check your billing dashboard for reset date")
    
    print("\n5. 🔧 USE A DIFFERENT OPENAI ACCOUNT:")
    print("   - Create a new OpenAI account")
    print("   - Get $5 free credits for new accounts")
    print("   - Use that API key temporarily")

def main():
    print("🚀 OpenAI API Key Status Checker")
    print("="*60)
    
    is_working = check_openai_status()
    
    if not is_working:
        suggest_solutions()
        
        print("\n" + "="*60)
        print("🔧 QUICK FIX: SWITCH TO GEMINI")
        print("="*60)
        print("To quickly fix this and test the image analysis:")
        print("1. Get a free Gemini API key: https://makersuite.google.com/app/apikey")
        print("2. Add to .env: GEMINI_API_KEY=your-gemini-key")
        print("3. Edit config.yaml: change 'provider: \"openai\"' to 'provider: \"gemini\"'")
        print("4. Restart Docker: docker-compose down && docker-compose up -d")
    else:
        print("\n✅ Your OpenAI API key is working fine!")
        print("The 429 error might be temporary. Try running your test again.")

if __name__ == "__main__":
    main()
