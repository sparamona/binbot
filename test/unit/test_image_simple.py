"""
Simple test for image storage system
"""

import sys
import os
from pathlib import Path
from PIL import Image

sys.path.append('.')

from storage.image_storage import get_image_storage


def test_image_storage_simple():
    """Simple test of image storage functionality"""
    print("🧪 Testing image storage (simple)...")
    
    try:
        # Get storage instance
        storage = get_image_storage()
        print("✅ Got image storage instance")
        
        # Create a simple test image in memory
        image = Image.new('RGB', (100, 100), color='red')
        test_image_path = './test_image.jpg'
        image.save(test_image_path, 'JPEG')
        print("✅ Created test image")
        
        # Test save
        image_id = storage.save_image(test_image_path, "test.jpg")
        print(f"✅ Saved image with ID: {image_id[:8]}...")
        
        # Test get path
        stored_path = storage.get_image_path(image_id)
        print(f"✅ Got stored path: {stored_path}")
        
        # Test metadata
        metadata = storage.get_image_metadata(image_id)
        print(f"✅ Got metadata: {metadata['original_filename']}")
        
        # Clean up
        os.unlink(test_image_path)  # Remove test image
        storage.delete_image(image_id)  # Remove stored image
        print("✅ Cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Testing image storage (simple version)...")
    print("=" * 50)
    
    success = test_image_storage_simple()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Image storage test passed!")
    else:
        print("❌ Image storage test failed!")
