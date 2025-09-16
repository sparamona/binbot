"""
OpenAI Vision API Integration for BinBot

This module provides image analysis capabilities using OpenAI's Vision API
for automatic item identification, description generation, and visual search.
"""

import base64
import os
from typing import Dict, Any, Optional, List
from openai import OpenAI
import json


class VisionService:
    """OpenAI Vision API service for image analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self.model = "gpt-4o"  # Updated OpenAI Vision model
        
    def initialize(self) -> bool:
        """Initialize the OpenAI client"""
        try:
            llm_config = self.config.get("llm", {})
            openai_config = llm_config.get("openai", {})
            api_key = openai_config.get("api_key")
            
            if not api_key:
                print("OpenAI API key not found in configuration")
                return False
                
            self.client = OpenAI(api_key=api_key)
            return True
            
        except Exception as e:
            print(f"Failed to initialize Vision service: {e}")
            return False
            
    def encode_image(self, image_path: str) -> Optional[str]:
        """Encode image to base64 string"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding image {image_path}: {e}")
            return None
            
    def identify_item(self, image_path: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Identify an item in an image and generate description
        
        Args:
            image_path: Path to the image file
            context: Optional context about where the item is located
            
        Returns:
            Dictionary with identification results
        """
        try:
            if not self.client:
                return {"success": False, "error": "Vision service not initialized"}
                
            # Encode image
            base64_image = self.encode_image(image_path)
            if not base64_image:
                return {"success": False, "error": "Failed to encode image"}
                
            # Prepare context message
            context_msg = ""
            if context:
                context_msg = f" This item is located in {context}."
                
            # Create prompt for item identification
            prompt = f"""Analyze this image and identify ALL distinct items shown. For each item, provide:

1. Item name (be specific but concise)
2. Description focusing on SPECIFIC OBSERVABLE FEATURES only (color, size, material, brand markings, unique characteristics) - avoid generic definitions of what the item is used for
3. Category (e.g., hardware, electronics, tools, etc.)
4. Key characteristics or features
5. Confidence level (1-10)

{context_msg}

Focus on what you can actually see in the image - specific colors, materials, shapes, text/logos, wear patterns, unique features, etc. Do NOT include generic explanations of what the item type is typically used for.

Please respond in JSON format with the following structure:
{{
    "items": [
        {{
            "item_name": "specific item name",
            "description": "specific observable features only - colors, materials, markings, condition, etc.",
            "category": "item category",
            "characteristics": ["specific_feature1", "specific_feature2", "specific_feature3"],
            "confidence": 8,
            "additional_notes": "any other specific observable details"
        }}
    ],
    "total_items": 1,
    "analysis_notes": "overall observations about the image"
}}

If there are multiple items, include each one as a separate object in the "items" array."""

            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1,  # Low temperature for consistent results
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Parse JSON response (should be clean JSON due to response_format)
            try:
                result = json.loads(content)
                result["success"] = True
                return result
            except json.JSONDecodeError:
                # Fallback if JSON parsing still fails
                return {
                    "success": True,
                    "item_name": "Unknown Item",
                    "description": content,
                    "category": "unknown",
                    "characteristics": [],
                    "confidence": 5,
                    "raw_response": content
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Vision API error: {str(e)}"
            }

    def search_by_image(self, image_path: str, search_query: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate search terms based on image content
        
        Args:
            image_path: Path to the image file
            search_query: Optional additional search context
            
        Returns:
            Dictionary with search terms and suggestions
        """
        try:
            if not self.client:
                return {"success": False, "error": "Vision service not initialized"}
                
            base64_image = self.encode_image(image_path)
            if not base64_image:
                return {"success": False, "error": "Failed to encode image"}
                
            search_context = ""
            if search_query:
                search_context = f" The user is looking for: {search_query}"
                
            prompt = f"""Analyze this image and generate search terms that would help find similar items in an inventory system. Please provide:

1. Primary search terms (most important keywords)
2. Secondary search terms (related keywords)
3. Category terms (broad categories this item belongs to)
4. Alternative names (other ways this item might be described)

{search_context}

Respond in JSON format:
{{
    "primary_terms": ["term1", "term2", "term3"],
    "secondary_terms": ["term4", "term5", "term6"],
    "categories": ["category1", "category2"],
    "alternatives": ["alt1", "alt2"],
    "suggested_query": "optimized search query string"
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300,
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            
            try:
                result = json.loads(content)
                result["success"] = True
                return result
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "primary_terms": ["unknown"],
                    "secondary_terms": [],
                    "categories": ["misc"],
                    "alternatives": [],
                    "suggested_query": search_query or "unknown item",
                    "raw_response": content
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Vision search error: {str(e)}"
            }
            
    def describe_for_accessibility(self, image_path: str) -> Dict[str, Any]:
        """
        Generate detailed description for accessibility/screen readers
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with accessibility description
        """
        try:
            if not self.client:
                return {"success": False, "error": "Vision service not initialized"}
                
            base64_image = self.encode_image(image_path)
            if not base64_image:
                return {"success": False, "error": "Failed to encode image"}
                
            prompt = """Provide a detailed description of this image for accessibility purposes. Include:

1. What objects are visible
2. Colors, shapes, and sizes
3. Positioning and arrangement
4. Any text or labels visible
5. Overall context and setting

Make the description clear and comprehensive for someone who cannot see the image."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            return {
                "success": True,
                "description": response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Accessibility description error: {str(e)}"
            }
