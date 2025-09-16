"""
Image Storage Management for BinBot

This module handles local filesystem-based image storage with organized
directory structure, compression, and metadata management.
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from PIL import Image, ImageOps
import hashlib
from datetime import datetime
import json


class ImageStorage:
    """Local filesystem-based image storage manager"""
    
    def __init__(self, base_path: str = "/app/data/images"):
        self.base_path = Path(base_path)
        self.setup_directories()
        
    def setup_directories(self):
        """Create the directory structure for image storage"""
        directories = [
            self.base_path,
            self.base_path / "images",
            self.base_path / "thumbnails" / "small",
            self.base_path / "thumbnails" / "medium",
            self.base_path / "metadata"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
    def save_image(self, image_data: bytes, item_id: str, bin_id: str,
                   filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Save an image to local storage with compression and thumbnail generation

        Args:
            image_data: Raw image bytes
            item_id: UUID of the item this image belongs to
            bin_id: Bin ID where the item is located
            filename: Original filename (optional)

        Returns:
            Dictionary with image metadata including paths and info
        """
        try:
            # Generate unique image ID
            image_id = str(uuid.uuid4())

            # Create hash for deduplication
            image_hash = hashlib.md5(image_data).hexdigest()

            # Determine file extension (always save as .jpg for consistency)
            ext = '.jpg'

            # Define paths using flat structure
            image_path = self.base_path / "images" / f"{image_id}{ext}"
            small_thumb_path = self.base_path / "thumbnails" / "small" / f"{image_id}.jpg"
            medium_thumb_path = self.base_path / "thumbnails" / "medium" / f"{image_id}.jpg"
            metadata_path = self.base_path / "metadata" / f"{image_id}.json"
                
            # Process and compress image
            from io import BytesIO
            with Image.open(BytesIO(image_data)) as img:
                # Auto-rotate based on EXIF data
                img = ImageOps.exif_transpose(img)

                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # Save compressed main image
                img.save(image_path, 'JPEG', quality=85, optimize=True)

                # Generate and save thumbnails
                thumbnail_small = self._generate_thumbnail(img, (150, 150))
                thumbnail_medium = self._generate_thumbnail(img, (400, 400))

                thumbnail_small.save(small_thumb_path, 'JPEG', quality=80, optimize=True)
                thumbnail_medium.save(medium_thumb_path, 'JPEG', quality=85, optimize=True)

                # Get image dimensions and size
                width, height = img.size
                file_size = os.path.getsize(image_path)
                
            # Create metadata
            metadata = {
                'image_id': image_id,
                'item_id': item_id,
                'bin_id': bin_id,
                'original_filename': filename,
                'file_hash': image_hash,
                'file_path': str(image_path.relative_to(self.base_path)),
                'thumbnail_small': str(small_thumb_path.relative_to(self.base_path)),
                'thumbnail_medium': str(medium_thumb_path.relative_to(self.base_path)),
                'width': width,
                'height': height,
                'file_size': file_size,
                'format': 'JPEG',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

            # Save metadata file
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            return metadata
            
        except Exception as e:
            raise Exception(f"Failed to save image: {str(e)}")
            
    def _generate_thumbnail(self, img: Image.Image, size: Tuple[int, int]) -> Image.Image:
        """Generate a thumbnail maintaining aspect ratio"""
        img_copy = img.copy()
        img_copy.thumbnail(size, Image.Resampling.LANCZOS)
        return img_copy
        
    def get_image_metadata(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific image"""
        metadata_path = self.base_path / "metadata" / f"{image_id}.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                return json.load(f)
        return None
        
    def get_item_images(self, item_id: str) -> List[Dict[str, Any]]:
        """Get all images for a specific item"""
        images = []
        metadata_dir = self.base_path / "metadata"

        if not metadata_dir.exists():
            return []

        # Search through all metadata files for this item_id
        for metadata_file in metadata_dir.glob("*.json"):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                if metadata.get('item_id') == item_id:
                    images.append(metadata)

        # Sort by creation date
        images.sort(key=lambda x: x['created_at'])
        return images
        
    def delete_image(self, image_id: str) -> bool:
        """Delete an image and all its associated files"""
        try:
            # Delete main image file
            main_image = self.base_path / "images" / f"{image_id}.jpg"
            if main_image.exists():
                main_image.unlink()

            # Delete thumbnails
            small_thumb = self.base_path / "thumbnails" / "small" / f"{image_id}.jpg"
            medium_thumb = self.base_path / "thumbnails" / "medium" / f"{image_id}.jpg"

            if small_thumb.exists():
                small_thumb.unlink()
            if medium_thumb.exists():
                medium_thumb.unlink()

            # Delete metadata file
            metadata_file = self.base_path / "metadata" / f"{image_id}.json"
            if metadata_file.exists():
                metadata_file.unlink()

            return True

        except Exception as e:
            print(f"Error deleting image {image_id}: {str(e)}")
            return False

    def update_image_metadata(self, image_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update metadata for an image

        Args:
            image_id: Image ID to update
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current metadata
            metadata = self.get_image_metadata(image_id)
            if not metadata:
                return False

            # Update metadata with provided fields
            metadata.update(updates)
            metadata['updated_at'] = datetime.utcnow().isoformat()

            # Save updated metadata
            metadata_path = self.base_path / "metadata" / f"{image_id}.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            return True

        except Exception as e:
            print(f"Error updating metadata for image {image_id}: {str(e)}")
            return False

    def get_image_path(self, image_id: str, size: str = "full") -> Optional[str]:
        """
        Get the file path for an image

        Args:
            image_id: Image ID
            size: "full", "medium", or "small"

        Returns:
            Absolute file path or None if not found
        """
        if size == "small":
            path = self.base_path / "thumbnails" / "small" / f"{image_id}.jpg"
        elif size == "medium":
            path = self.base_path / "thumbnails" / "medium" / f"{image_id}.jpg"
        else:
            path = self.base_path / "images" / f"{image_id}.jpg"

        return str(path) if path.exists() else None
            
    def cleanup_orphaned_images(self, valid_item_ids: List[str]) -> int:
        """
        Clean up images for items that no longer exist

        Args:
            valid_item_ids: List of item IDs that still exist in the database

        Returns:
            Number of orphaned images cleaned up
        """
        cleaned_count = 0
        metadata_dir = self.base_path / "metadata"

        if not metadata_dir.exists():
            return 0

        valid_item_ids_set = set(valid_item_ids)

        for metadata_file in metadata_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)

                item_id = metadata.get('item_id')
                if item_id and item_id not in valid_item_ids_set:
                    # This image belongs to an item that no longer exists
                    image_id = metadata.get('image_id')
                    if image_id and self.delete_image(image_id):
                        cleaned_count += 1

            except Exception as e:
                print(f"Error processing metadata file {metadata_file}: {str(e)}")

        return cleaned_count
        
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        stats = {
            'total_images': 0,
            'total_size_bytes': 0,
            'items_with_images': 0,
            'thumbnail_count': 0
        }

        # Count images and calculate sizes
        images_dir = self.base_path / "images"
        if images_dir.exists():
            image_files = list(images_dir.glob("*.jpg"))
            stats['total_images'] = len(image_files)

            for image_file in image_files:
                stats['total_size_bytes'] += image_file.stat().st_size

        # Count items with images
        metadata_dir = self.base_path / "metadata"
        if metadata_dir.exists():
            item_ids_with_images = set()
            for metadata_file in metadata_dir.glob("*.json"):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    item_id = metadata.get('item_id')
                    if item_id:
                        item_ids_with_images.add(item_id)
                except:
                    continue
            stats['items_with_images'] = len(item_ids_with_images)

        # Count thumbnails
        for thumb_dir in ['small', 'medium']:
            thumb_path = self.base_path / "thumbnails" / thumb_dir
            if thumb_path.exists():
                stats['thumbnail_count'] += len(list(thumb_path.glob("*.jpg")))

        return stats
