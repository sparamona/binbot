"""
Simple vision analysis using Gemini
"""

import google.generativeai as genai
from PIL import Image
from typing import List, Dict
import json

from config.settings import GEMINI_API_KEY


class VisionService:
    """Simple vision service using Gemini"""

    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')

        # Define JSON schema for inventory items
        self.item_schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["name", "description"]
                    }
                }
            },
            "required": ["items"]
        }

    def analyze_image(self, image_path: str) -> List[Dict[str, str]]:
        """Analyze image and return structured list of items using JSON schema"""
        # Load and resize image for analysis
        image = Image.open(image_path)

        # Resize if too large (keep it simple - max 1024px)
        if max(image.size) > 1024:
            ratio = 1024 / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        # Create prompt for structured output
        prompt = """
        Analyze this image and identify individual items that could be stored in bins.

        Focus on distinct, separate objects that would be inventory items.
        For each item, provide a clear name and brief description including any distinguishing features.
        """

        # Create model with structured output
        structured_model = genai.GenerativeModel(
            self.model.model_name,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=self.item_schema
            )
        )

        # Send to Gemini with structured output
        response = structured_model.generate_content([prompt, image])

        # Parse the structured JSON response
        result = json.loads(response.text)
        return result.get("items", [])


# Global vision service instance
_vision_service = None


def get_vision_service() -> VisionService:
    """Get the global vision service"""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service
