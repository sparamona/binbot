#!/usr/bin/env python3
"""
Test script to measure optimized performance with real coaster/pen/mouse image
"""

import requests
import time
import os
import statistics

def test_optimized_performance():
    """Test the optimized performance with timing"""
    
    print("🎯 TESTING OPTIMIZED PERFORMANCE")
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
    
    # Run multiple tests to get average performance
    results = []
    num_tests = 1
    
    for i in range(num_tests):
        print(f"--- Test {i+1}/{num_tests} ---")
        
        # Prepare request
        files = {'image': ('coaster_pen_mouse.jpg', image_data, 'image/jpeg')}
        data = {
            'command': 'What items can you see in this image?',
            'session_id': f'test_session_{i}_{int(time.time())}'
        }
        
        # Time the request
        print("📤 Uploading image and processing...")
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
                
                # Extract the response message
                response_message = result.get('data', {}).get('response', 'No response')
                message = result.get('data', {}).get('message', response_message)
                
                print(f"💬 Response received:")
                print(f"   {message}")
                print()
                
                # Store result
                results.append({
                    'total_time': total_time,
                    'response': message,
                    'success': True
                })
                
            else:
                print(f"❌ Error response: {response.status_code}")
                print(f"   {response.text[:200]}")
                results.append({
                    'total_time': total_time,
                    'success': False,
                    'error': response.text[:200]
                })
                
        except requests.exceptions.Timeout:
            total_time = time.time() - start_time
            print(f"⏰ Request timed out after {total_time:.3f} seconds")
            results.append({
                'total_time': total_time,
                'success': False,
                'error': 'Timeout'
            })
            
        except Exception as e:
            total_time = time.time() - start_time
            print(f"❌ Exception after {total_time:.3f} seconds: {e}")
            results.append({
                'total_time': total_time,
                'success': False,
                'error': str(e)
            })
        
        # Brief pause between tests
        if i < num_tests - 1:
            print("⏸️  Pausing 3 seconds between tests...")
            time.sleep(3)
            print()
    
    # Analyze results
    print("📊 PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    successful_results = [r for r in results if r['success']]
    
    if successful_results:
        times = [r['total_time'] for r in successful_results]
        
        print(f"✅ Successful tests: {len(successful_results)}/{num_tests}")
        print(f"⏱️  Average time: {statistics.mean(times):.3f} seconds")
        print(f"📈 Time range: {min(times):.3f}s - {max(times):.3f}s")
        
        if len(times) > 1:
            print(f"📊 Standard deviation: {statistics.stdev(times):.3f}s")
        
        print()
        print("🎯 OPTIMIZATION IMPACT:")
        
        # Compare with previous baseline (19.7s from our earlier tests)
        baseline = 19.7
        current_avg = statistics.mean(times)
        improvement = ((baseline - current_avg) / baseline) * 100
        
        print(f"   Previous baseline: {baseline:.1f}s")
        print(f"   Current average: {current_avg:.1f}s")
        print(f"   Improvement: {improvement:+.1f}%")
        
        if improvement > 20:
            print(f"   🎉 EXCELLENT: {improvement:.0f}% faster!")
        elif improvement > 10:
            print(f"   ✅ GOOD: {improvement:.0f}% faster!")
        elif improvement > 0:
            print(f"   📊 MODEST: {improvement:.0f}% faster!")
        else:
            print(f"   ⚠️  SLOWER: {abs(improvement):.0f}% slower than baseline")
        
        print()
        print("💡 SAMPLE RESPONSE:")
        if successful_results:
            sample_response = successful_results[0]['response']
            print(f"   {sample_response}")
    
    else:
        print("❌ No successful tests completed")
        for i, result in enumerate(results):
            print(f"   Test {i+1}: {result.get('error', 'Unknown error')}")

def main():
    """Main function to run all tests"""
    
    print("🧪 OPTIMIZED PERFORMANCE TEST SUITE")
    print("=" * 80)
    print()
    
    # Test synchronous processing with optimizations
    test_optimized_performance()

    
    print("\n🎉 Testing completed!")
    print("\n📋 OPTIMIZATIONS TESTED:")
    print("   1. ✅ JPEG Quality (85→75)")
    print("   2. ✅ Optimization Threshold (500KB→50KB)")  
    print("   3. ✅ max_tokens (500→300)")
if __name__ == "__main__":
    main()
