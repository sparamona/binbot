"""
LLM Vision API Integration for BinBot

This module provides image analysis capabilities using various LLM providers
for automatic item identification, description generation, and visual search.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from utils.image_optimizer import optimize_for_vision_api
from .client import LLMClient

logger = logging.getLogger(__name__)


class VisionService:
    """LLM Vision API service for image analysis"""

    def __init__(self, config: Dict[str, Any], llm_client: Optional[LLMClient] = None):
        self.config = config
        self.llm_client = llm_client

    def initialize(self) -> bool:
        """Initialize the vision service"""
        if not self.llm_client:
            print("LLM client not provided to VisionService")
            return False

        if not self.llm_client.validate_connection():
            print("LLM client not properly initialized")
            return False

        print("Vision service initialized successfully")
        return True

    def _load_and_optimize_image(self, image_path: str) -> Optional[bytes]:
        """Load and optimize image for LLM API"""
        try:
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()

            # Optimize image for LLM API call (original stays stored as-is)
            optimized_data = optimize_for_vision_api(image_data, profile="balanced")

            # Log optimization results
            original_size = len(image_data)
            optimized_size = len(optimized_data)
            if optimized_size < original_size:
                reduction = ((original_size - optimized_size) / original_size) * 100
                logger.info(f"Image optimized for LLM API: {original_size:,} → {optimized_size:,} bytes ({reduction:.1f}% reduction)")
            else:
                logger.debug(f"Image already optimal for LLM API: {original_size:,} bytes")

            return optimized_data
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            return None

    async def identify_item(self, image_path: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Identify an item in an image and generate description

        Args:
            image_path: Path to the image file
            context: Optional context about where the item is located

        Returns:
            Dictionary with identification results
        """
        try:
            if not self.llm_client:
                return {"success": False, "error": "Vision service not initialized"}

            # Load and optimize image
            image_data = self._load_and_optimize_image(image_path)
            if not image_data:
                return {"success": False, "error": "Failed to load image"}

            # Prepare context message
            context_msg = ""
            if context:
                context_msg = f" This item is located in {context}."

            # Create prompt for item identification
            prompt = f"""Analyze this image and identify ALL distinct items shown. For each item, provide:

1. Item name (be specific but concise)
2. Description with SPECIFIC OBSERVABLE FEATURES (color, size, material, brand markings, unique characteristics, condition, wear patterns, text/logos, etc.)

{context_msg}

Focus on what you can actually see in the image. Include distinguishing features that would help someone identify this specific item. Avoid generic explanations of what the item type is used for.

Please respond in JSON format with the following structure:
{{
    "items": [
        {{
            "item_name": "specific item name",
            "description": "detailed description with specific observable features - colors, materials, markings, condition, size, unique characteristics, etc."
        }}
    ],
    "total_items": 1,
    "analysis_notes": "overall observations about the image"
}}

If there are multiple items, include each one as a separate object in the "items" array."""

            # Make API call using centralized client
            response = await self.llm_client.analyze_image(
                image_data=image_data,
                prompt=prompt,
                max_tokens=300,
                temperature=0.1,
                response_format="json_object"
            )

            if not response.success:
                return {"success": False, "error": response.error}

            # If we got structured data, use it; otherwise parse the content
            if response.structured_data:
                result = response.structured_data
                result["success"] = True
                return result
            elif response.content:
                try:
                    result = json.loads(response.content)
                    result["success"] = True
                    return result
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return {
                        "success": True,
                        "items": [{
                            "item_name": "Unknown Item",
                            "description": response.content
                        }],
                        "total_items": 1,
                        "raw_response": response.content
                    }
            else:
                return {"success": False, "error": "No content in response"}

        except Exception as e:
            return {
                "success": False,
                "error": f"Vision API error: {str(e)}"
            }

    async def search_by_image(self, image_path: str, search_query: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate search terms based on image content

        Args:
            image_path: Path to the image file
            search_query: Optional additional search context

        Returns:
            Dictionary with search terms and suggestions
        """
        try:
            if not self.llm_client:
                return {"success": False, "error": "Vision service not initialized"}

            # Load and optimize image
            image_data = self._load_and_optimize_image(image_path)
            if not image_data:
                return {"success": False, "error": "Failed to load image"}

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

            # Make API call using centralized client
            response = await self.llm_client.analyze_image(
                image_data=image_data,
                prompt=prompt,
                max_tokens=300,
                temperature=0.2,
                response_format="json_object"
            )

            if not response.success:
                return {"success": False, "error": response.error}

            # If we got structured data, use it; otherwise parse the content
            if response.structured_data:
                result = response.structured_data
                result["success"] = True
                return result
            elif response.content:
                try:
                    result = json.loads(response.content)
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
                        "raw_response": response.content
                    }
            else:
                return {"success": False, "error": "No content in response"}

        except Exception as e:
            return {
                "success": False,
                "error": f"Vision search error: {str(e)}"
            }

    async def describe_for_accessibility(self, image_path: str) -> Dict[str, Any]:
        """
        Generate detailed description for accessibility/screen readers

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary with accessibility description
        """
        try:
            if not self.llm_client:
                return {"success": False, "error": "Vision service not initialized"}

            # Load and optimize image
            image_data = self._load_and_optimize_image(image_path)
            if not image_data:
                return {"success": False, "error": "Failed to load image"}
                
            prompt = """Provide a detailed description of this image for accessibility purposes. Include:

1. What objects are visible
2. Colors, shapes, and sizes
3. Positioning and arrangement
4. Any text or labels visible
5. Overall context and setting

Make the description clear and comprehensive for someone who cannot see the image."""

            # Make API call using centralized client
            response = await self.llm_client.analyze_image(
                image_data=image_data,
                prompt=prompt,
                max_tokens=400,
                temperature=0.3
            )

            if not response.success:
                return {"success": False, "error": response.error}

            return {
                "success": True,
                "description": response.content or "No description available",
                "purpose": "accessibility"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Accessibility description error: {str(e)}"
            }
