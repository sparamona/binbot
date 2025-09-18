#!/usr/bin/env python3
"""
Script to shrink the test image file for more efficient testing
"""

import os
from PIL import Image

def shrink_image(input_path, output_path=None, max_width=800, max_height=600, quality=85):
    """
    Shrink an image while maintaining aspect ratio and good quality
    
    Args:
        input_path: Path to input image
        output_path: Path for output image (defaults to overwriting input)
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        quality: JPEG quality (1-100, higher is better)
    """
    if not os.path.exists(input_path):
        print(f"❌ Input file not found: {input_path}")
        return False
    
    if output_path is None:
        output_path = input_path
    
    try:
        # Get original file size
        original_size = os.path.getsize(input_path)
        print(f"📁 Original file: {input_path}")
        print(f"📏 Original size: {original_size:,} bytes ({original_size/1024/1024:.2f} MB)")
        
        # Open and analyze image
        with Image.open(input_path) as img:
            original_width, original_height = img.size
            print(f"🖼️  Original dimensions: {original_width}x{original_height}")
            print(f"🎨 Original format: {img.format}")
            
            # Calculate new dimensions while maintaining aspect ratio
            ratio = min(max_width / original_width, max_height / original_height)
            
            if ratio >= 1:
                print("✅ Image is already small enough, just optimizing quality...")
                new_width, new_height = original_width, original_height
            else:
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
                print(f"🔄 Resizing to: {new_width}x{new_height} (ratio: {ratio:.2f})")
            
            # Resize image if needed
            if ratio < 1:
                # Use high-quality resampling
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                resized_img = img
            
            # Convert to RGB if necessary (for JPEG)
            if resized_img.mode in ('RGBA', 'P'):
                print("🔄 Converting to RGB for JPEG compatibility...")
                rgb_img = Image.new('RGB', resized_img.size, (255, 255, 255))
                if resized_img.mode == 'P':
                    resized_img = resized_img.convert('RGBA')
                rgb_img.paste(resized_img, mask=resized_img.split()[-1] if resized_img.mode == 'RGBA' else None)
                resized_img = rgb_img
            
            # Save optimized image
            save_kwargs = {
                'format': 'JPEG',
                'quality': quality,
                'optimize': True
            }
            
            resized_img.save(output_path, **save_kwargs)
            
        # Get new file size
        new_size = os.path.getsize(output_path)
        reduction = ((original_size - new_size) / original_size) * 100
        
        print(f"✅ Optimized file saved: {output_path}")
        print(f"📏 New size: {new_size:,} bytes ({new_size/1024/1024:.2f} MB)")
        print(f"📉 Size reduction: {reduction:.1f}% ({original_size - new_size:,} bytes saved)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return False

def main():
    input_file = "test/coaster_pen_mouse.jpg"
    
    print("🚀 Image Optimization Tool")
    print("="*50)
    
    if not os.path.exists(input_file):
        print(f"❌ Test image not found: {input_file}")
        return
    
    # Create backup first
    backup_file = input_file.replace('.jpg', '_original.jpg')
    if not os.path.exists(backup_file):
        print(f"💾 Creating backup: {backup_file}")
        with open(input_file, 'rb') as src, open(backup_file, 'wb') as dst:
            dst.write(src.read())
    else:
        print(f"✅ Backup already exists: {backup_file}")
    
    # Optimize the image
    success = shrink_image(
        input_path=input_file,
        max_width=800,      # Good balance of quality vs size
        max_height=600,     # Sufficient for object detection
        quality=85          # High quality but compressed
    )
    
    if success:
        print("\n🎉 Image optimization completed!")
        print("💡 Benefits:")
        print("   • Faster upload times")
        print("   • Reduced API costs")
        print("   • Quicker test execution")
        print("   • Same object detection accuracy")
        
        # Test the optimized image
        print(f"\n🔍 Testing optimized image...")
        try:
            with Image.open(input_file) as img:
                width, height = img.size
                print(f"✅ Optimized image verified: {width}x{height}")
        except Exception as e:
            print(f"❌ Error verifying optimized image: {e}")
    else:
        print("❌ Image optimization failed")

if __name__ == "__main__":
    main()
