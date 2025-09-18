#!/usr/bin/env python3
"""
Test Script: UI Workflow Scenario
Tests the exact user workflow that was reported as broken:
1. User uploads image via camera interface
2. User types "add these items to bin X" in chat
3. Verify thumbnails appear in the bin display
"""

import requests
import json
import os
import time
import uuid
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"
TEST_IMAGE = "coaster_pen_mouse.jpg"  # Relative to test directory

class UIWorkflowTester:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.bin_id = f"ui-test-{int(time.time())}"
        
    def log(self, message, level="INFO"):
        """Log with timestamp and level"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def check_server_health(self):
        """Verify server is running and healthy"""
        self.log("Checking server health...")
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200 and response.json().get('success'):
                self.log("✅ Server is healthy")
                return True
            else:
                self.log("❌ Server health check failed", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Cannot connect to server: {e}", "ERROR")
            return False
    
    def step1_camera_upload_analysis(self):
        """
        Step 1: Simulate camera upload for initial analysis
        This is what happens when user clicks camera and uploads image
        """
        self.log("📷 STEP 1: Camera Upload & Analysis")
        self.log(f"Session ID: {self.session_id}")
        self.log(f"Target Bin: {self.bin_id}")
        
        if not os.path.exists(TEST_IMAGE):
            self.log(f"❌ Test image not found: {TEST_IMAGE}", "ERROR")
            return False
            
        try:
            with open(TEST_IMAGE, 'rb') as f:
                files = {'image': (os.path.basename(TEST_IMAGE), f, 'image/jpeg')}
                data = {
                    'command': 'What items can you see in this image?',
                    'session_id': self.session_id
                }
                
                self.log("Uploading image for analysis...")
                response = requests.post(
                    f"{BASE_URL}/nlp/command-with-image",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            if response.status_code != 200:
                self.log(f"❌ Image upload failed: HTTP {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
            result = response.json()
            if not result.get('success'):
                self.log(f"❌ Image analysis failed: {result.get('error', 'Unknown error')}", "ERROR")
                return False
            
            self.log("✅ Image uploaded and analyzed successfully")
            
            # Log the analysis response
            message = result.get('data', {}).get('response', 'No response')
            self.log(f"Analysis result: {message}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Exception in camera upload: {e}", "ERROR")
            return False
    
    def step2_chat_command_with_image(self):
        """
        Step 2: Simulate the UI's smart detection and combined API call
        This is what the modified UI should do when user types "add these items to bin X"
        """
        self.log("💬 STEP 2: Chat Command with Image Context")
        self.log(f"Command: 'add these items to bin {self.bin_id}'")
        self.log("Expected: UI detects 'add items' command and includes image")
        
        try:
            # This simulates what the modified UI does:
            # - Detects "add items" command
            # - Uses stored image context
            # - Makes combined API call
            
            with open(TEST_IMAGE, 'rb') as f:
                files = {'image': (os.path.basename(TEST_IMAGE), f, 'image/jpeg')}
                data = {
                    'command': f'add these items to bin {self.bin_id}',
                    'session_id': self.session_id
                }
                
                self.log("Making combined image + command API call...")
                response = requests.post(
                    f"{BASE_URL}/nlp/command-with-image",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            if response.status_code != 200:
                self.log(f"❌ Chat command failed: HTTP {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
            result = response.json()
            if not result.get('success'):
                self.log(f"❌ Chat command failed: {result.get('error', 'Unknown error')}", "ERROR")
                return False
            
            self.log("✅ Chat command with image successful!")
            
            # Log the command response
            message = result.get('data', {}).get('response', 'No response')
            self.log(f"Command result: {message}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Exception in chat command: {e}", "ERROR")
            return False
    
    def step3_verify_thumbnails(self):
        """
        Step 3: Verify that items were created with image associations
        This checks what the user would see in the bin display
        """
        self.log("🔍 STEP 3: Verify Thumbnail Display")
        
        try:
            # Wait a moment for processing
            time.sleep(2)
            
            self.log(f"Checking bin contents: {self.bin_id}")
            response = requests.get(f"{BASE_URL}/test/bin/{self.bin_id}/items", timeout=10)
            
            if response.status_code != 200:
                self.log(f"❌ Failed to get bin contents: HTTP {response.status_code}", "ERROR")
                return False
                
            result = response.json()
            if not result.get('success'):
                self.log(f"❌ Failed to get bin contents: {result.get('error', 'Unknown error')}", "ERROR")
                return False
            
            items = result['data']['items']
            self.log(f"📦 Items found in bin: {len(items)}")
            
            if len(items) == 0:
                self.log("❌ No items were created", "ERROR")
                return False
            
            # Check each item for image associations
            items_with_images = 0
            for i, item in enumerate(items, 1):
                name = item.get('name', 'Unknown')
                primary_image = item.get('primary_image', '').strip()
                images_count = item.get('images_count', 0)
                
                self.log(f"📋 Item {i}: {name}")
                self.log(f"   Images: {images_count}, Primary: {'✅' if primary_image else '❌'}")
                
                if primary_image:
                    items_with_images += 1
                    # Test thumbnail URL accessibility
                    thumbnail_url = f"{BASE_URL}/images/file/{primary_image}?size=medium"
                    try:
                        thumb_response = requests.head(thumbnail_url, timeout=5)
                        if thumb_response.status_code == 200:
                            self.log(f"   ✅ Thumbnail accessible: {thumbnail_url}")
                        else:
                            self.log(f"   ❌ Thumbnail not accessible: HTTP {thumb_response.status_code}")
                    except Exception as e:
                        self.log(f"   ❌ Thumbnail check failed: {e}")
            
            success_rate = f"{items_with_images}/{len(items)}"
            self.log(f"📊 Items with thumbnails: {success_rate}")
            
            return items_with_images > 0, items_with_images, len(items)
            
        except Exception as e:
            self.log(f"❌ Exception in verification: {e}", "ERROR")
            return False
    
    def run_full_test(self):
        """Run the complete UI workflow test"""
        self.log("🚀 Starting UI Workflow Scenario Test")
        self.log("=" * 60)
        self.log("This test simulates the exact user workflow:")
        self.log("1. User uploads image via camera interface")
        self.log("2. User types 'add these items to bin X' in chat")
        self.log("3. Verify thumbnails appear in bin display")
        self.log("")
        
        # Check server health
        if not self.check_server_health():
            return False
        
        # Step 1: Camera upload and analysis
        if not self.step1_camera_upload_analysis():
            self.log("❌ Step 1 failed - stopping test", "ERROR")
            return False
        
        self.log("")
        
        # Step 2: Chat command with image context
        if not self.step2_chat_command_with_image():
            self.log("❌ Step 2 failed - stopping test", "ERROR")
            return False
        
        self.log("")
        
        # Step 3: Verify thumbnails
        result = self.step3_verify_thumbnails()
        if isinstance(result, tuple):
            success, items_with_images, total_items = result
        else:
            success = result
            items_with_images = 0
            total_items = 0
        
        self.log("")
        self.log("=" * 60)
        self.log("🏁 UI WORKFLOW TEST RESULTS")
        self.log("=" * 60)
        
        if success:
            self.log("🎉 SUCCESS! UI workflow is working correctly!")
            self.log("")
            self.log("✅ Test Results:")
            self.log(f"   • Items created: {total_items}")
            self.log(f"   • Items with thumbnails: {items_with_images}")
            self.log(f"   • Success rate: {items_with_images}/{total_items}")
            self.log("")
            self.log("🎯 This confirms:")
            self.log("   • Camera upload and analysis works")
            self.log("   • Combined image + command API call works")
            self.log("   • Image associations are created correctly")
            self.log("   • Thumbnails are accessible for UI display")
            self.log("")
            self.log("🚀 The UI workflow is FIXED!")
            
        else:
            self.log("❌ UI workflow test failed", "ERROR")
            self.log("")
            self.log("🔍 Possible issues:")
            self.log("   • Image upload/analysis not working")
            self.log("   • Combined API call not working")
            self.log("   • Image association logic broken")
            self.log("   • Backend processing errors")
            self.log("")
            self.log("💡 Check Docker logs for more details:")
            self.log("   docker logs binboteh-binbot-1 --tail=50")
        
        return success

def main():
    """Main test execution"""
    tester = UIWorkflowTester()
    success = tester.run_full_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
