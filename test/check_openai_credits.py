#!/usr/bin/env python3
"""
Script to check OpenAI API credit balance and usage
"""

import os
import requests
from datetime import datetime, timedelta
import json

def get_api_key():
    """Get API key from .env file or environment"""
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
    
    return api_key

def check_billing_info(api_key):
    """Check billing information and credit balance"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print("🔄 Checking billing information...")
    
    # Check subscription info
    try:
        response = requests.get('https://api.openai.com/v1/dashboard/billing/subscription', 
                              headers=headers, timeout=10)
        print(f"Subscription endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            subscription = response.json()
            print("✅ Subscription Info:")
            print(f"   Plan: {subscription.get('plan', {}).get('title', 'Unknown')}")
            print(f"   Hard limit: ${subscription.get('hard_limit_usd', 'Unknown')}")
            print(f"   Soft limit: ${subscription.get('soft_limit_usd', 'Unknown')}")
            print(f"   System hard limit: ${subscription.get('system_hard_limit_usd', 'Unknown')}")
            
        elif response.status_code == 401:
            print("❌ API key is invalid or expired")
            return False
        elif response.status_code == 429:
            print("❌ Rate limited - too many requests")
            return False
        else:
            print(f"❌ Subscription check failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking subscription: {e}")
    
    # Check usage for current month
    try:
        # Get current month dates
        now = datetime.now()
        start_date = now.replace(day=1).strftime('%Y-%m-%d')
        end_date = now.strftime('%Y-%m-%d')
        
        print(f"\n🔄 Checking usage from {start_date} to {end_date}...")
        
        response = requests.get(
            f'https://api.openai.com/v1/dashboard/billing/usage?start_date={start_date}&end_date={end_date}',
            headers=headers, timeout=10
        )
        print(f"Usage endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            usage = response.json()
            total_usage = usage.get('total_usage', 0) / 100  # Convert from cents to dollars
            print("✅ Usage Info:")
            print(f"   Total usage this month: ${total_usage:.2f}")
            
            # Show daily breakdown if available
            daily_costs = usage.get('daily_costs', [])
            if daily_costs:
                print("   Recent daily usage:")
                for day in daily_costs[-7:]:  # Last 7 days
                    date = day.get('timestamp')
                    cost = day.get('line_items', [{}])[0].get('cost', 0) / 100
                    print(f"     {date}: ${cost:.2f}")
                    
        elif response.status_code == 401:
            print("❌ API key is invalid for usage endpoint")
            return False
        elif response.status_code == 429:
            print("❌ Rate limited on usage endpoint")
            return False
        else:
            print(f"❌ Usage check failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking usage: {e}")
    
    return True

def check_credit_grants(api_key):
    """Check for any credit grants (free credits)"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print("\n🔄 Checking credit grants...")
    
    try:
        # Get current month dates
        now = datetime.now()
        start_date = (now - timedelta(days=90)).strftime('%Y-%m-%d')  # Last 90 days
        end_date = now.strftime('%Y-%m-%d')
        
        response = requests.get(
            f'https://api.openai.com/v1/dashboard/billing/credit_grants?start_date={start_date}&end_date={end_date}',
            headers=headers, timeout=10
        )
        print(f"Credit grants endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            grants = response.json()
            print("✅ Credit Grants:")
            
            total_granted = grants.get('total_granted', 0) / 100
            total_used = grants.get('total_used', 0) / 100
            total_available = grants.get('total_available', 0) / 100
            
            print(f"   Total granted: ${total_granted:.2f}")
            print(f"   Total used: ${total_used:.2f}")
            print(f"   Total available: ${total_available:.2f}")
            
            # Show individual grants
            grant_data = grants.get('data', [])
            if grant_data:
                print("   Individual grants:")
                for grant in grant_data:
                    grant_amount = grant.get('grant_amount', 0) / 100
                    used_amount = grant.get('used_amount', 0) / 100
                    remaining = grant_amount - used_amount
                    expires = grant.get('expires_at')
                    print(f"     ${grant_amount:.2f} grant, ${used_amount:.2f} used, ${remaining:.2f} remaining (expires: {expires})")
            
        else:
            print(f"❌ Credit grants check failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking credit grants: {e}")

def main():
    print("🚀 OpenAI Credit Balance and Usage Checker")
    print("="*60)
    
    api_key = get_api_key()
    if not api_key:
        print("❌ No OpenAI API key found")
        print("Make sure OPENAI_API_KEY is set in your .env file or environment")
        return
    
    print(f"🔑 Using API key: {api_key[:10]}...{api_key[-4:]}")
    
    # Check billing info and usage
    success = check_billing_info(api_key)
    
    if success:
        # Check credit grants (free credits)
        check_credit_grants(api_key)
        
        print("\n" + "="*60)
        print("💡 WHAT THIS MEANS:")
        print("="*60)
        print("• If 'Total available' > $0, you have free credits remaining")
        print("• If 'Total available' = $0, you need to add paid credits")
        print("• Check your hard limit vs usage to see remaining paid balance")
        print("• 429 errors occur when you exceed your available balance")
        
        print("\n🔗 USEFUL LINKS:")
        print("• Billing Dashboard: https://platform.openai.com/account/billing")
        print("• Usage Dashboard: https://platform.openai.com/account/usage")
        print("• Add Credits: https://platform.openai.com/account/billing/overview")
    
    print("\n🏁 Credit check completed!")

if __name__ == "__main__":
    main()
