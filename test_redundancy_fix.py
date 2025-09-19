#!/usr/bin/env python3
"""
Test script to verify the redundant OpenAI call optimization
"""

import requests
import time
import os

def test_redundancy_optimization():
    """Test that simple vision queries skip redundant LLM processing"""
    
    print("🎯 TESTING REDUNDANCY OPTIMIZATION")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server health check failed: {response.status_code}")
            return
        print("✅ Server is running and healthy")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Check if test image exists
    test_image_path = 'test/coaster_pen_mouse.jpg'
    if not os.path.exists(test_image_path):
        print(f"❌ Test image not found: {test_image_path}")
        return
    
    # Read the test image
    with open(test_image_path, 'rb') as f:
        image_data = f.read()
    
    print(f"📸 Using test image: {test_image_path}")
    print(f"📏 Image size: {len(image_data):,} bytes ({len(image_data)/1024:.1f} KB)")
    print()
    
    # Test 1: Simple vision query (should use optimization)
    print("--- Test 1: Simple Vision Query (Optimized) ---")
    test_simple_vision_query(image_data)
    
    print()
    
    # Test 2: Action command (should use normal processing)
    print("--- Test 2: Action Command (Normal Processing) ---")
    test_action_command(image_data)

def test_simple_vision_query(image_data):
    """Test a simple vision query that should skip redundant processing"""
    
    files = {'image': ('coaster_pen_mouse.jpg', image_data, 'image/jpeg')}
    data = {
        'command': 'What items can you see in this image?',
        'session_id': f'simple_test_{int(time.time())}'
    }
    
    print("📤 Testing simple vision query...")
    print(f"💬 Command: '{data['command']}'")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            'http://localhost:8000/nlp/upload-image',
            files=files,
            data=data,
            timeout=60
        )
        
        total_time = time.time() - start_time
        
        print(f"⏱️  Total time: {total_time:.3f} seconds")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if optimization was applied
            optimization_applied = result.get('data', {}).get('optimization_applied')
            time_saved = result.get('data', {}).get('time_saved')
            
            if optimization_applied:
                print(f"🚀 OPTIMIZATION APPLIED: {optimization_applied}")
                print(f"⚡ Time saved: {time_saved}")
            else:
                print("⚠️  No optimization detected (normal processing used)")
            
            # Extract the response message
            response_message = result.get('data', {}).get('response', 'No response')
            
            print(f"💬 Response preview:")
            print(f"   {response_message[:150]}...")
            
            # Expected: Should be much faster (~8-10s instead of 15-20s)
            if total_time < 12:
                print(f"✅ FAST RESPONSE: {total_time:.1f}s (optimization likely working)")
            elif total_time < 18:
                print(f"📊 MODERATE: {total_time:.1f}s (some improvement)")
            else:
                print(f"⚠️  SLOW: {total_time:.1f}s (optimization may not be working)")
                
        else:
            print(f"❌ Error response: {response.status_code}")
            print(f"   {response.text[:200]}")
            
    except Exception as e:
        total_time = time.time() - start_time
        print(f"❌ Exception after {total_time:.3f}s: {e}")

def test_action_command(image_data):
    """Test an action command that should use normal processing"""
    
    files = {'image': ('coaster_pen_mouse.jpg', image_data, 'image/jpeg')}
    data = {
        'command': 'add these items to bin 5',
        'session_id': f'action_test_{int(time.time())}'
    }
    
    print("📤 Testing action command...")
    print(f"💬 Command: '{data['command']}'")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            'http://localhost:8000/nlp/upload-image',
            files=files,
            data=data,
            timeout=60
        )
        
        total_time = time.time() - start_time
        
        print(f"⏱️  Total time: {total_time:.3f} seconds")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if optimization was applied (should NOT be for action commands)
            optimization_applied = result.get('data', {}).get('optimization_applied')
            
            if optimization_applied:
                print(f"⚠️  UNEXPECTED: Optimization applied to action command")
            else:
                print("✅ CORRECT: Normal processing used for action command")
            
            # Extract the response message
            response_message = result.get('data', {}).get('response', 'No response')
            
            print(f"💬 Response preview:")
            print(f"   {response_message[:150]}...")
            
            # Expected: Should take normal time (15-20s) since it needs function calling
            if total_time > 12:
                print(f"✅ NORMAL PROCESSING: {total_time:.1f}s (expected for action commands)")
            else:
                print(f"⚠️  UNEXPECTEDLY FAST: {total_time:.1f}s (may not have processed correctly)")
                
        else:
            print(f"❌ Error response: {response.status_code}")
            print(f"   {response.text[:200]}")
            
    except Exception as e:
        total_time = time.time() - start_time
        print(f"❌ Exception after {total_time:.3f}s: {e}")

def main():
    """Main function to run redundancy optimization tests"""
    
    print("🧪 REDUNDANCY OPTIMIZATION TEST")
    print("=" * 80)
    print()
    print("This test verifies that simple vision queries like 'What can you see?'")
    print("skip the redundant LLM call and return vision results directly.")
    print()
    
    test_redundancy_optimization()
    
    print("\n🎉 Testing completed!")
    print("\n📋 EXPECTED RESULTS:")
    print("   • Simple vision queries: ~8-10s (optimization applied)")
    print("   • Action commands: ~15-20s (normal processing)")
    print("   • Time saved: ~37% for simple queries")

if __name__ == "__main__":
    main()
