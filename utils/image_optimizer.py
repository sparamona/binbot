"""
Image optimization utility for OpenAI Vision API
Automatically optimizes images to reduce costs and improve performance
"""

import io
import logging
from typing import Tuple, Optional
from PIL import Image, ImageOps
import os

logger = logging.getLogger(__name__)

class ImageOptimizer:
    """
    Optimizes images for OpenAI Vision API to reduce costs and improve performance
    """
    
    # Optimization profiles for different use cases
    PROFILES = {
        "fast": {
            "max_width": 800,
            "max_height": 600,
            "quality": 80,
            "max_file_size": 300_000,  # 300KB
            "description": "Fastest processing, good for simple object detection"
        },
        "balanced": {
            "max_width": 1024,
            "max_height": 768,
            "quality": 85,
            "max_file_size": 500_000,  # 500KB
            "description": "Best balance of quality and performance (recommended)"
        },
        "quality": {
            "max_width": 1280,
            "max_height": 960,
            "quality": 90,
            "max_file_size": 800_000,  # 800KB
            "description": "Highest quality, for detailed analysis"
        }
    }
    
    def __init__(self, profile: str = "balanced"):
        """
        Initialize optimizer with specified profile
        
        Args:
            profile: Optimization profile ("fast", "balanced", or "quality")
        """
        if profile not in self.PROFILES:
            raise ValueError(f"Unknown profile: {profile}. Available: {list(self.PROFILES.keys())}")
        
        self.profile = profile
        self.settings = self.PROFILES[profile]
        logger.info(f"ImageOptimizer initialized with '{profile}' profile")
    
    def should_optimize(self, image_data: bytes) -> bool:
        """
        Check if image needs optimization based on file size
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            True if optimization is recommended
        """
        file_size = len(image_data)
        max_size = self.settings["max_file_size"]
        
        should_opt = file_size > max_size
        
        if should_opt:
            logger.info(f"Image size {file_size:,} bytes exceeds threshold {max_size:,} bytes - optimization recommended")
        else:
            logger.debug(f"Image size {file_size:,} bytes is within threshold {max_size:,} bytes - no optimization needed")
            
        return should_opt
    
    def get_optimal_dimensions(self, original_width: int, original_height: int) -> Tuple[int, int]:
        """
        Calculate optimal dimensions while maintaining aspect ratio
        
        Args:
            original_width: Original image width
            original_height: Original image height
            
        Returns:
            Tuple of (optimal_width, optimal_height)
        """
        max_width = self.settings["max_width"]
        max_height = self.settings["max_height"]
        
        # Calculate scaling ratio to fit within max dimensions
        width_ratio = max_width / original_width
        height_ratio = max_height / original_height
        ratio = min(width_ratio, height_ratio, 1.0)  # Don't upscale
        
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        
        return new_width, new_height
    
    def optimize_image(self, image_data: bytes, force: bool = False) -> Tuple[bytes, dict]:
        """
        Optimize image for OpenAI Vision API
        
        Args:
            image_data: Raw image bytes
            force: Force optimization even if not needed
            
        Returns:
            Tuple of (optimized_image_bytes, optimization_stats)
        """
        original_size = len(image_data)
        
        # Check if optimization is needed
        if not force and not self.should_optimize(image_data):
            return image_data, {
                "optimized": False,
                "original_size": original_size,
                "final_size": original_size,
                "reduction_percent": 0.0,
                "reason": "Below size threshold"
            }
        
        try:
            # Open and analyze image
            with Image.open(io.BytesIO(image_data)) as img:
                original_width, original_height = img.size
                original_format = img.format
                
                logger.info(f"Optimizing image: {original_width}x{original_height} {original_format}, {original_size:,} bytes")
                
                # Fix image orientation based on EXIF data
                img = ImageOps.exif_transpose(img)
                
                # Calculate optimal dimensions
                new_width, new_height = self.get_optimal_dimensions(original_width, original_height)
                
                # Resize if needed
                if (new_width, new_height) != (original_width, original_height):
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    logger.info(f"Resized to: {new_width}x{new_height}")
                
                # Convert to RGB if necessary (for JPEG compatibility)
                if img.mode in ('RGBA', 'P', 'LA'):
                    # Create white background for transparency
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode in ('RGBA', 'LA'):
                        rgb_img.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                    else:
                        rgb_img.paste(img)
                    img = rgb_img
                    logger.debug("Converted to RGB format")
                
                # Save optimized image
                output_buffer = io.BytesIO()
                img.save(
                    output_buffer,
                    format='JPEG',
                    quality=self.settings["quality"],
                    optimize=True,
                    progressive=True  # Better compression for larger images
                )
                
                optimized_data = output_buffer.getvalue()
                final_size = len(optimized_data)
                reduction_percent = ((original_size - final_size) / original_size) * 100
                
                stats = {
                    "optimized": True,
                    "original_size": original_size,
                    "final_size": final_size,
                    "reduction_percent": reduction_percent,
                    "original_dimensions": (original_width, original_height),
                    "final_dimensions": (new_width, new_height),
                    "quality": self.settings["quality"],
                    "profile": self.profile
                }
                
                logger.info(f"Optimization complete: {final_size:,} bytes ({reduction_percent:.1f}% reduction)")
                
                return optimized_data, stats
                
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            # Return original image if optimization fails
            return image_data, {
                "optimized": False,
                "original_size": original_size,
                "final_size": original_size,
                "reduction_percent": 0.0,
                "error": str(e)
            }
    
    def optimize_file(self, input_path: str, output_path: Optional[str] = None) -> dict:
        """
        Optimize image file
        
        Args:
            input_path: Path to input image file
            output_path: Path for output file (defaults to overwriting input)
            
        Returns:
            Optimization statistics
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if output_path is None:
            output_path = input_path
        
        # Read input file
        with open(input_path, 'rb') as f:
            image_data = f.read()
        
        # Optimize
        optimized_data, stats = self.optimize_image(image_data, force=True)
        
        # Write output file
        with open(output_path, 'wb') as f:
            f.write(optimized_data)
        
        stats["input_path"] = input_path
        stats["output_path"] = output_path
        
        return stats

# Convenience functions for easy integration
def optimize_for_vision_api(image_data: bytes, profile: str = "balanced") -> bytes:
    """
    Quick optimization function for OpenAI Vision API
    
    Args:
        image_data: Raw image bytes
        profile: Optimization profile
        
    Returns:
        Optimized image bytes
    """
    optimizer = ImageOptimizer(profile)
    optimized_data, _ = optimizer.optimize_image(image_data)
    return optimized_data

def get_optimization_stats(image_data: bytes, profile: str = "balanced") -> dict:
    """
    Get optimization statistics without actually optimizing
    
    Args:
        image_data: Raw image bytes
        profile: Optimization profile
        
    Returns:
        Statistics about what optimization would do
    """
    optimizer = ImageOptimizer(profile)
    _, stats = optimizer.optimize_image(image_data, force=True)
    return stats

# Example usage
if __name__ == "__main__":
    # Test with the coaster/pen/mouse image
    test_image_path = "../test/coaster_pen_mouse.jpg"
    
    if os.path.exists(test_image_path):
        optimizer = ImageOptimizer("balanced")
        stats = optimizer.optimize_file(test_image_path, test_image_path + "_optimized.jpg")
        
        print("Optimization Results:")
        print(f"  Original size: {stats['original_size']:,} bytes")
        print(f"  Final size: {stats['final_size']:,} bytes")
        print(f"  Reduction: {stats['reduction_percent']:.1f}%")
        print(f"  Dimensions: {stats['original_dimensions']} → {stats['final_dimensions']}")
    else:
        print(f"Test image not found: {test_image_path}")
