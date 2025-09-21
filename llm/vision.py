"""
Simple vision analysis using Gemini with new google-genai SDK
"""

from google import genai
from google.genai import types
from PIL import Image
from typing import List, Dict
import json

from config.settings import GEMINI_API_KEY


class VisionService:
    """Simple vision service using Gemini with new SDK"""

    def __init__(self):
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

    def _create_client(self) -> genai.Client:
        """Create a fresh Gemini client for each request"""
        return genai.Client(api_key=GEMINI_API_KEY)

    def analyze_image(self, image_path: str) -> List[Dict[str, str]]:
        """Analyze image and return structured list of items using JSON schema"""
        # Load and resize image for analysis
        image = Image.open(image_path)

        # Resize if too large (keep it simple - max 1024px)
        if max(image.size) > 1024:
            ratio = 1024 / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        # Convert PIL Image to bytes for the API (with RGBA->RGB conversion)
        import io
        img_byte_arr = io.BytesIO()

        # Convert RGBA to RGB if necessary (PNG with transparency -> JPEG)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create a white background for transparent images
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        elif image.mode not in ('RGB', 'L'):
            # Convert any other modes to RGB
            image = image.convert('RGB')

        image.save(img_byte_arr, format='JPEG', quality=95)
        img_bytes = img_byte_arr.getvalue()

        # Create prompt for structured output
        prompt = """
        Analyze this image and identify individual items that could be stored in bins.

        Focus on distinct, separate objects that would be inventory items.
        For each item, provide a clear name and brief description including any distinguishing features.
        """

        # Create content with image and text for new SDK
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(text=prompt),
                    types.Part(inline_data=types.Blob(
                        mime_type="image/jpeg",
                        data=img_bytes  # Pass bytes data instead of PIL Image
                    ))
                ]
            )
        ]

        # Configure for JSON output
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=self.item_schema
        )

        # Create fresh client for this request
        client = self._create_client()

        # Generate structured response using new SDK
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=contents,
            config=config
        )

        # Parse the structured JSON response
        try:
            result = json.loads(response.text)
            return result.get("items", [])
        except json.JSONDecodeError:
            return []


# Global vision service instance
_vision_service = None


def get_vision_service() -> VisionService:
    """Get the global vision service"""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service
