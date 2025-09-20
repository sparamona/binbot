"""
Basic vision service test - simple image analysis
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set memory mode for clean testing
os.environ['STORAGE_MODE'] = 'memory'

from llm.vision import get_vision_service


def test_basic_vision_analysis():
    """Test basic vision service with test image"""
    
    print("👁️ Testing Basic Vision Analysis")
    print("=" * 40)
    
    # Check if test image exists
    test_image_path = Path(__file__).parent.parent / "coaster_pen_mouse.jpg"
    if not test_image_path.exists():
        print(f"❌ Test image not found: {test_image_path}")
        return False
    
    print(f"📸 Using test image: {test_image_path.name}")
    
    try:
        # Initialize vision service
        vision_service = get_vision_service()
        print("✅ Vision service initialized")
        
        # Read image data
        with open(test_image_path, 'rb') as f:
            image_data = f.read()
        
        print(f"📸 Image loaded: {len(image_data)} bytes")
        
        # Test 1: Simple object identification
        print("\n🔍 Test 1: Simple object identification")
        result1 = vision_service.analyze_image(
            image_data,
            "What objects do you see in this image? List them briefly."
        )
        print(f"📋 Result: {result1}")
        
        # Test 2: Inventory-focused analysis
        print("\n📦 Test 2: Inventory-focused analysis")
        result2 = vision_service.analyze_image(
            image_data,
            "Identify items in this image that could be inventory items. For each item, provide a name and brief description."
        )
        print(f"📋 Result: {result2}")
        
        # Test 3: Count items
        print("\n🔢 Test 3: Count items")
        result3 = vision_service.analyze_image(
            image_data,
            "How many distinct objects are visible in this image?"
        )
        print(f"📋 Result: {result3}")
        
        # Verify we got reasonable responses
        if all(len(result) > 10 for result in [result1, result2, result3]):
            print("\n✅ All vision analysis tests passed!")
            print("✅ Vision service is working correctly")
            return True
        else:
            print("\n❌ Some vision analysis tests returned short responses")
            return False
            
    except Exception as e:
        print(f"\n❌ Vision analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("👁️ BinBot Basic Vision Test")
    print("Tests basic image analysis functionality")
    print()
    
    success = test_basic_vision_analysis()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Vision analysis test passed!")
        print("The vision service can analyze images correctly.")
    else:
        print("❌ Vision analysis test failed!")
        print("Check the error messages above for details.")
