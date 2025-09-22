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

        print(f"📸 Testing with image: {test_image_path}")

        # Test the actual production method
        print("\n🔍 Testing production method: analyze_image")
        analyzed_items = vision_service.analyze_image(str(test_image_path))

        print(f"📋 Production analysis result:")
        print(f"   Found {len(analyzed_items)} items:")
        for i, item in enumerate(analyzed_items, 1):
            print(f"   {i}. {item.get('name', 'Unknown')} - {item.get('description', 'No description')}")

        # Verify we got reasonable results
        if len(analyzed_items) > 0 and all(
            isinstance(item, dict) and
            'name' in item and
            'description' in item and
            len(item['name']) > 0 and
            len(item['description']) > 0
            for item in analyzed_items
        ):
            print("\n✅ Production vision analysis test passed!")
            print("✅ Vision service is working correctly")
            return True
        else:
            print("\n❌ Production vision analysis test failed")
            print(f"   Items: {analyzed_items}")
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
