"""
Tests for image storage system
"""

import sys
import tempfile
import os
from pathlib import Path
from PIL import Image

sys.path.append('.')

from storage.image_storage import ImageStorage


def create_test_image(width: int = 100, height: int = 100) -> str:
    """Create a test image file and return its path"""
    # Create a simple test image
    image = Image.new('RGB', (width, height), color='red')
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    image.save(temp_file.name, 'JPEG')
    temp_file.close()
    
    return temp_file.name


def test_image_storage_basic_operations():
    """Test basic image storage operations"""
    print("🧪 Testing image storage basic operations...")
    
    # Create temporary storage directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Override storage path for testing
        storage = ImageStorage()
        storage.storage_path = Path(temp_dir)
        storage.storage_path.mkdir(exist_ok=True)
        
        # Create test image
        test_image_path = create_test_image()
        
        try:
            # Save image
            image_id = storage.save_image(test_image_path, "test_image.jpg")
            assert image_id is not None
            assert len(image_id) > 0
            print(f"✅ Saved image with ID: {image_id[:8]}...")
            
            # Get image path
            stored_path = storage.get_image_path(image_id)
            assert stored_path is not None
            assert os.path.exists(stored_path)
            print("✅ Retrieved image path")
            
            # Get metadata
            metadata = storage.get_image_metadata(image_id)
            assert metadata is not None
            assert metadata['image_id'] == image_id
            assert metadata['original_filename'] == "test_image.jpg"
            print("✅ Retrieved image metadata")
            
            # Update metadata
            storage.update_image_metadata(image_id, {'item_id': 'test-item-123'})
            updated_metadata = storage.get_image_metadata(image_id)
            assert updated_metadata['item_id'] == 'test-item-123'
            print("✅ Updated image metadata")
            
            # Delete image
            deleted = storage.delete_image(image_id)
            assert deleted is True
            assert not os.path.exists(stored_path)
            assert storage.get_image_metadata(image_id) is None
            print("✅ Deleted image")
            
        finally:
            # Clean up test image
            if os.path.exists(test_image_path):
                os.unlink(test_image_path)
    
    return True


def test_image_resize_for_analysis():
    """Test image resizing for analysis"""
    print("🧪 Testing image resize for analysis...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = ImageStorage()
        storage.storage_path = Path(temp_dir)
        
        # Create large test image
        large_image_path = create_test_image(2000, 1500)  # Large image
        
        try:
            # Test resize
            resized_path = storage.resize_image_for_analysis(large_image_path, max_size=1024)
            assert resized_path != large_image_path  # Should be different path
            assert os.path.exists(resized_path)
            
            # Check resized dimensions
            resized_image = Image.open(resized_path)
            assert max(resized_image.size) <= 1024
            print(f"✅ Resized image to {resized_image.size}")
            
            # Test with small image (should not resize)
            small_image_path = create_test_image(500, 300)
            not_resized_path = storage.resize_image_for_analysis(small_image_path, max_size=1024)
            assert not_resized_path == small_image_path  # Should be same path
            print("✅ Small image not resized")
            
        finally:
            # Clean up
            for path in [large_image_path, resized_path if 'resized_path' in locals() else None]:
                if path and os.path.exists(path):
                    os.unlink(path)
            if 'small_image_path' in locals() and os.path.exists(small_image_path):
                os.unlink(small_image_path)
    
    return True


def test_global_instance():
    """Test global image storage instance"""
    print("🧪 Testing global image storage instance...")
    
    from storage.image_storage import get_image_storage
    
    storage1 = get_image_storage()
    storage2 = get_image_storage()
    
    assert storage1 is storage2  # Should be same instance
    print("✅ Global instance works correctly")
    
    return True


if __name__ == "__main__":
    print("🧪 Testing image storage system...")
    print("=" * 50)
    
    try:
        test_image_storage_basic_operations()
        print()
        test_image_resize_for_analysis()
        print()
        test_global_instance()
        
        print("\n" + "=" * 50)
        print("🎉 All image storage tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
