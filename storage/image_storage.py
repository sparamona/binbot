"""
Simple local image storage for BinBot
"""

import os
import uuid
import shutil
import json
from pathlib import Path
from typing import Dict, Optional
from PIL import Image

from config.settings import IMAGES_PATH, STORAGE_MODE


class ImageStorage:
    """Simple image storage with memory/persistent modes"""

    def __init__(self):
        if STORAGE_MODE == 'memory':
            # In-memory storage for testing
            self._image_data: Dict[str, bytes] = {}
            self._metadata: Dict[str, Dict] = {}  # Keep metadata for memory mode
            self.storage_path = None
        else:
            # Persistent file storage for production
            self.storage_path = Path(IMAGES_PATH)
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self._image_data = None
    
    def save_image(self, file_path: str, original_filename: str = "") -> str:
        """Save an image file and return image_id (always converts to JPG)"""
        image_id = str(uuid.uuid4())

        if STORAGE_MODE == 'memory':
            # In-memory storage - convert to JPG
            image = Image.open(file_path)
            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Save as JPG to bytes
            import io
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='JPEG', quality=85, optimize=True)
            image_bytes = img_bytes.getvalue()

            self._image_data[image_id] = image_bytes

            # Store minimal metadata for memory mode
            self._metadata[image_id] = {
                'image_id': image_id,
                'filename': f"{image_id}.jpg",
                'file_size': len(image_bytes)
            }
        else:
            # Persistent file storage - convert to JPG
            image = Image.open(file_path)
            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if image.mode != 'RGB':
                image = image.convert('RGB')

            dest_path = self.storage_path / f"{image_id}.jpg"
            image.save(dest_path, format='JPEG', quality=85, optimize=True)

        return image_id
    
    def get_image_path(self, image_id: str) -> Optional[str]:
        """Get the file path for an image (always JPG)"""
        if STORAGE_MODE == 'memory':
            if image_id in self._metadata:
                return f"memory://{image_id}.jpg"
            return None
        else:
            # All images are stored as JPG
            file_path = self.storage_path / f"{image_id}.jpg"
            if file_path.exists():
                return str(file_path)
            return None

    def get_image_data(self, image_id: str) -> Optional[bytes]:
        """Get image data (for in-memory mode)"""
        if STORAGE_MODE == 'memory' and image_id in self._image_data:
            return self._image_data[image_id]
        return None
    
    def get_image_metadata(self, image_id: str) -> Optional[Dict]:
        """Get metadata for an image (always JPG)"""
        if STORAGE_MODE == 'memory':
            return self._metadata.get(image_id)
        else:
            # Check if JPG file exists on disk
            file_path = self.storage_path / f"{image_id}.jpg"
            if file_path.exists():
                return {
                    'image_id': image_id,
                    'filename': f"{image_id}.jpg",
                    'file_path': str(file_path),
                    'file_size': file_path.stat().st_size
                }
            return None
    
    def update_image_metadata(self, image_id: str, metadata: Dict):
        """Update metadata for an image"""
        if image_id in self._metadata:
            self._metadata[image_id].update(metadata)
    
    def delete_image(self, image_id: str) -> bool:
        """Delete an image file and metadata"""
        if image_id not in self._metadata:
            return False

        if STORAGE_MODE == 'memory':
            # Remove from in-memory storage
            if image_id in self._image_data:
                del self._image_data[image_id]
        else:
            # Delete file from disk
            file_path = Path(self._metadata[image_id]['file_path'])
            if file_path.exists():
                file_path.unlink()

        # Remove metadata
        del self._metadata[image_id]
        return True
    
    def resize_image_for_analysis(self, image_path: str, max_size: int = 1024) -> str:
        """Resize image for LLM analysis and return path to resized version"""
        image = Image.open(image_path)
        
        # Check if resize is needed
        if max(image.size) <= max_size:
            return image_path
        
        # Calculate new size
        ratio = max_size / max(image.size)
        new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
        
        # Resize image
        resized_image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save resized version
        base_path = Path(image_path)
        resized_path = base_path.parent / f"{base_path.stem}_resized{base_path.suffix}"
        resized_image.save(resized_path, quality=85, optimize=True)
        
        return str(resized_path)


# Global image storage instance
_image_storage = None


def get_image_storage() -> ImageStorage:
    """Get the global image storage instance"""
    global _image_storage
    if _image_storage is None:
        _image_storage = ImageStorage()
    return _image_storage
