#!/usr/bin/env python3
"""
Test script to isolate vision service issues
"""

import sys
from pathlib import Path

def test_vision_service():
    """Test the vision service directly"""
    
    # Test image path
    image_path = Path("test/coaster_pen_mouse.jpg")
    
    if not image_path.exists():
        print(f"Error: Test image not found at {image_path}")
        return
    
    print(f"Testing vision service with: {image_path}")
    
    try:
        print("Importing vision service...")
        from llm.vision import get_vision_service
        
        print("Creating vision service instance...")
        vision_service = get_vision_service()
        
        print("Analyzing image...")
        result = vision_service.analyze_image(str(image_path))
        
        print(f"Analysis result: {result}")
        print(f"Result type: {type(result)}")
        print(f"Number of items found: {len(result) if result else 0}")
        
        if result:
            for i, item in enumerate(result):
                print(f"Item {i+1}: {item}")
        
    except Exception as e:
        print(f"Error in vision service: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vision_service()
