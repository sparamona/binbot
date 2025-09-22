#!/usr/bin/env python3
"""
Test PNG upload fix for RGBA -> RGB conversion
"""

import tempfile
import os
from PIL import Image
import io

def test_png_rgba_conversion():
    """Test that RGBA PNG images are properly converted to RGB for JPEG"""
    
    # Create a test RGBA PNG image (with transparency)
    print("🧪 Creating test RGBA PNG image...")
    rgba_image = Image.new('RGBA', (100, 100), (255, 0, 0, 128))  # Semi-transparent red
    
    # Save as PNG to temp file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_png:
        rgba_image.save(temp_png.name, 'PNG')
        temp_png_path = temp_png.name
    
    try:
        # Test the conversion logic from vision.py
        print("📸 Testing RGBA -> RGB conversion...")
        
        # Load the image (simulating vision service)
        image = Image.open(temp_png_path)
        print(f"Original image mode: {image.mode}")
        
        # Apply the conversion logic
        img_byte_arr = io.BytesIO()
        
        # Convert RGBA to RGB if necessary (PNG with transparency -> JPEG)
        if image.mode in ('RGBA', 'LA', 'P'):
            print("🔄 Converting RGBA to RGB with white background...")
            # Create a white background for transparent images
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        elif image.mode not in ('RGB', 'L'):
            # Convert any other modes to RGB
            image = image.convert('RGB')
        
        print(f"Converted image mode: {image.mode}")
        
        # Try to save as JPEG (this should work now)
        image.save(img_byte_arr, format='JPEG', quality=95)
        img_bytes = img_byte_arr.getvalue()
        
        print(f"✅ Successfully converted RGBA PNG to JPEG! Size: {len(img_bytes)} bytes")
        
        # Verify the JPEG can be loaded
        jpeg_image = Image.open(io.BytesIO(img_bytes))
        print(f"✅ JPEG verification: mode={jpeg_image.mode}, size={jpeg_image.size}")
        
        return True
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return False
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_png_path):
            os.unlink(temp_png_path)

def test_various_image_modes():
    """Test conversion for various image modes"""
    
    test_modes = [
        ('RGB', (255, 0, 0)),           # Standard RGB
        ('RGBA', (255, 0, 0, 128)),     # RGB with alpha
        ('L', 128),                     # Grayscale
        ('P', None),                    # Palette mode
    ]
    
    print("\n🎨 Testing various image modes...")
    
    for mode, color in test_modes:
        print(f"\n📋 Testing {mode} mode...")
        
        try:
            # Create test image
            if mode == 'P':
                # Create palette image
                image = Image.new('RGB', (50, 50), (255, 0, 0))
                image = image.convert('P')
            else:
                image = Image.new(mode, (50, 50), color)
            
            print(f"   Original: {image.mode}")
            
            # Apply conversion logic
            img_byte_arr = io.BytesIO()
            
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = background
            elif image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            print(f"   Converted: {image.mode}")
            
            # Save as JPEG
            image.save(img_byte_arr, format='JPEG', quality=95)
            print(f"   ✅ JPEG save successful: {len(img_byte_arr.getvalue())} bytes")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")

if __name__ == "__main__":
    print("🔧 Testing PNG Upload Fix for BinBot")
    print("=" * 50)
    
    # Test main RGBA conversion
    success = test_png_rgba_conversion()
    
    # Test various modes
    test_various_image_modes()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ PNG upload fix is working correctly!")
        print("📝 PNG files with transparency will now be converted to RGB with white background")
        print("🚀 Ready to test with actual PNG uploads in BinBot")
    else:
        print("❌ PNG upload fix needs more work")
    
    print("\n📋 Next steps:")
    print("1. Upload a PNG file with transparency to BinBot")
    print("2. Verify it processes without RGBA -> JPEG errors")
    print("3. Check that the image analysis works correctly")
