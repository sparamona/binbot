"""
Simple local image storage for BinBot
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Dict, Optional
from PIL import Image

from config.settings import IMAGES_PATH, STORAGE_MODE


class ImageStorage:
    """Simple image storage with memory/persistent modes"""

    def __init__(self):
        self._metadata: Dict[str, Dict] = {}

        if STORAGE_MODE == 'memory':
            # In-memory storage for testing
            self._image_data: Dict[str, bytes] = {}
            self.storage_path = None
        else:
            # Persistent file storage for production
            self.storage_path = Path(IMAGES_PATH)
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self._image_data = None
    
    def save_image(self, file_path: str, original_filename: str = "") -> str:
        """Save an image file and return image_id"""
        image_id = str(uuid.uuid4())

        # Determine file extension
        if original_filename:
            ext = Path(original_filename).suffix.lower()
        else:
            ext = Path(file_path).suffix.lower()

        if not ext:
            ext = '.jpg'  # Default extension

        if STORAGE_MODE == 'memory':
            # In-memory storage
            with open(file_path, 'rb') as f:
                image_bytes = f.read()
            self._image_data[image_id] = image_bytes

            # Store metadata
            self._metadata[image_id] = {
                'image_id': image_id,
                'filename': f"{image_id}{ext}",
                'original_filename': original_filename,
                'file_path': f"memory://{image_id}{ext}",
                'file_size': len(image_bytes)
            }
        else:
            # Persistent file storage
            dest_path = self.storage_path / f"{image_id}{ext}"
            shutil.copy2(file_path, dest_path)

            # Store metadata
            self._metadata[image_id] = {
                'image_id': image_id,
                'filename': dest_path.name,
                'original_filename': original_filename,
                'file_path': str(dest_path),
                'file_size': dest_path.stat().st_size
            }

        return image_id
    
    def get_image_path(self, image_id: str) -> Optional[str]:
        """Get the file path for an image"""
        if image_id in self._metadata:
            return self._metadata[image_id]['file_path']
        return None

    def get_image_data(self, image_id: str) -> Optional[bytes]:
        """Get image data (for in-memory mode)"""
        if STORAGE_MODE == 'memory' and image_id in self._image_data:
            return self._image_data[image_id]
        return None
    
    def get_image_metadata(self, image_id: str) -> Optional[Dict]:
        """Get metadata for an image"""
        return self._metadata.get(image_id)
    
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
