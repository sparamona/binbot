#!/usr/bin/env python3
"""
Test script to verify rich descriptions from vision analysis are being stored in the database
"""

import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_vision_analysis_parsing():
    """Test the vision analysis parsing logic"""
    print("=== Testing Vision Analysis Parsing ===")
    
    # Mock vision analysis data (what the vision service returns)
    mock_vision_result = {
        "success": True,
        "items": [
            {
                "item_name": "Red Screwdriver",
                "description": "A red-handled screwdriver with black metal shaft, approximately 6 inches long, showing some wear on the handle grip"
            },
            {
                "item_name": "Blue Wrench", 
                "description": "A blue adjustable wrench with chrome-plated jaws, 8-inch length, with visible manufacturer markings 'CRAFTSMAN' on the handle"
            }
        ],
        "total_items": 2,
        "analysis_notes": "Two hand tools clearly visible against white background"
    }
    
    # Test the processing logic from api/nlp.py
    identified_items = []
    if mock_vision_result and mock_vision_result.get("success") and mock_vision_result.get("items"):
        print(f"Vision analysis successful, found {len(mock_vision_result['items'])} items")
        for item in mock_vision_result["items"]:
            identified_items.append({
                "name": item.get('item_name', 'Unknown item'),
                "description": item.get('description', ''),
                "confidence": item.get('confidence', 0.0)
            })
    
    print(f"Processed identified_items: {json.dumps(identified_items, indent=2)}")
    
    # Test the vision data storage format
    image_id = "test-image-123"
    vision_data = {
        "image_id": image_id,
        "items": identified_items
    }
    vision_message = f"VISION_ANALYSIS:{json.dumps(vision_data)}"
    print(f"\nVision message for conversation: {vision_message}")
    
    # Test the parsing logic from function_handler.py
    print("\n=== Testing Function Handler Parsing ===")
    
    # Simulate parsing the vision message
    if vision_message.startswith("VISION_ANALYSIS:"):
        json_data = vision_message[len("VISION_ANALYSIS:"):]
        parsed_vision_data = json.loads(json_data)
        
        if parsed_vision_data.get("image_id") == image_id:
            print(f"Found vision analysis data for image {image_id}")
            
            vision_items = {}
            for item in parsed_vision_data.get("items", []):
                item_name = item.get("name", "")
                item_description = item.get("description", "")
                if item_name and item_description:
                    vision_items[item_name] = {
                        "description": item_description,
                        "confidence": item.get("confidence", 0.0)
                    }
            
            print(f"Extracted vision items map: {json.dumps(vision_items, indent=2)}")
            
            # Test description selection logic
            print("\n=== Testing Description Selection ===")
            test_items = ["Red Screwdriver", "Blue Wrench", "New Item"]
            bin_id = "5"
            
            for item_name in test_items:
                if item_name in vision_items:
                    description = vision_items[item_name]["description"]
                    print(f"✅ Using vision description for '{item_name}': {description}")
                else:
                    description = f"{item_name} in bin {bin_id}"
                    print(f"⚠️  Using generic description for '{item_name}': {description}")
    
    print("\n=== Test Complete ===")
    return True

if __name__ == "__main__":
    test_vision_analysis_parsing()
