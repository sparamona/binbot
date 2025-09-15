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
            self.base_path / "items",
            self.base_path / "bins", 
            self.base_path / "thumbnails" / "small",
            self.base_path / "thumbnails" / "medium",
            self.base_path / "temp"
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
            
            # Determine file extension
            if filename:
                ext = Path(filename).suffix.lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                    ext = '.jpg'
            else:
                ext = '.jpg'
                
            # Create item directory
            item_dir = self.base_path / "items" / item_id
            item_dir.mkdir(parents=True, exist_ok=True)
            
            # Save original image
            original_path = item_dir / f"{image_id}_original{ext}"
            with open(original_path, 'wb') as f:
                f.write(image_data)
                
            # Process and compress image
            with Image.open(original_path) as img:
                # Auto-rotate based on EXIF data
                img = ImageOps.exif_transpose(img)
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                    
                # Save compressed version
                compressed_path = item_dir / f"{image_id}{ext}"
                img.save(compressed_path, 'JPEG', quality=85, optimize=True)
                
                # Generate thumbnails
                thumbnail_small = self._generate_thumbnail(img, (150, 150))
                thumbnail_medium = self._generate_thumbnail(img, (400, 400))
                
                # Save thumbnails
                small_thumb_path = self.base_path / "thumbnails" / "small" / f"{image_id}.jpg"
                medium_thumb_path = self.base_path / "thumbnails" / "medium" / f"{image_id}.jpg"
                
                thumbnail_small.save(small_thumb_path, 'JPEG', quality=80, optimize=True)
                thumbnail_medium.save(medium_thumb_path, 'JPEG', quality=85, optimize=True)
                
                # Get image dimensions and size
                width, height = img.size
                file_size = os.path.getsize(compressed_path)
                
            # Create metadata
            metadata = {
                'image_id': image_id,
                'item_id': item_id,
                'bin_id': bin_id,
                'original_filename': filename,
                'file_hash': image_hash,
                'file_path': str(compressed_path.relative_to(self.base_path)),
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
            metadata_path = item_dir / f"{image_id}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            # Clean up original if different from compressed
            if original_path != compressed_path:
                original_path.unlink()
                
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
        # Search for metadata file across all item directories
        for item_dir in (self.base_path / "items").iterdir():
            if item_dir.is_dir():
                metadata_path = item_dir / f"{image_id}_metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        return json.load(f)
        return None
        
    def get_item_images(self, item_id: str) -> List[Dict[str, Any]]:
        """Get all images for a specific item"""
        item_dir = self.base_path / "items" / item_id
        if not item_dir.exists():
            return []
            
        images = []
        for metadata_file in item_dir.glob("*_metadata.json"):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                images.append(metadata)
                
        # Sort by creation date
        images.sort(key=lambda x: x['created_at'])
        return images
        
    def delete_image(self, image_id: str) -> bool:
        """Delete an image and all its associated files"""
        metadata = self.get_image_metadata(image_id)
        if not metadata:
            return False
            
        try:
            item_id = metadata['item_id']
            item_dir = self.base_path / "items" / item_id
            
            # Delete main image file
            main_image = item_dir / Path(metadata['file_path']).name
            if main_image.exists():
                main_image.unlink()
                
            # Delete thumbnails
            small_thumb = self.base_path / metadata['thumbnail_small']
            medium_thumb = self.base_path / metadata['thumbnail_medium']
            
            if small_thumb.exists():
                small_thumb.unlink()
            if medium_thumb.exists():
                medium_thumb.unlink()
                
            # Delete metadata file
            metadata_file = item_dir / f"{image_id}_metadata.json"
            if metadata_file.exists():
                metadata_file.unlink()
                
            return True
            
        except Exception as e:
            print(f"Error deleting image {image_id}: {str(e)}")
            return False

    def update_item_id(self, image_id: str, old_item_id: str, new_item_id: str) -> bool:
        """
        Update the item ID for an image (used when moving from temp ID to real ID)

        Args:
            image_id: Image ID to update
            old_item_id: Current item ID
            new_item_id: New item ID to set

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current metadata
            metadata = self.get_image_metadata(image_id)
            if not metadata:
                return False

            # Update metadata
            metadata['item_id'] = new_item_id
            metadata['updated_at'] = datetime.utcnow().isoformat()

            # Find the metadata file
            old_item_dir = self.base_path / "items" / old_item_id
            metadata_path = old_item_dir / f"{image_id}_metadata.json"

            if metadata_path.exists():
                # Save updated metadata
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)

                # Move files to new item directory if different
                if old_item_id != new_item_id:
                    new_item_dir = self.base_path / "items" / new_item_id
                    new_item_dir.mkdir(parents=True, exist_ok=True)

                    # Move all files for this image
                    for file_path in old_item_dir.glob(f"{image_id}*"):
                        new_file_path = new_item_dir / file_path.name
                        file_path.rename(new_file_path)

                    # Update file paths in metadata
                    metadata['file_path'] = str((new_item_dir / f"{image_id}.jpg").relative_to(self.base_path))

                    # Save metadata again with updated paths
                    new_metadata_path = new_item_dir / f"{image_id}_metadata.json"
                    with open(new_metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=2)

                return True
            else:
                return False

        except Exception as e:
            print(f"Error updating item ID for image {image_id}: {str(e)}")
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
        metadata = self.get_image_metadata(image_id)
        if not metadata:
            return None
            
        if size == "small":
            return str(self.base_path / metadata['thumbnail_small'])
        elif size == "medium":
            return str(self.base_path / metadata['thumbnail_medium'])
        else:
            return str(self.base_path / metadata['file_path'])
            
    def cleanup_orphaned_images(self, valid_item_ids: List[str]) -> int:
        """
        Clean up images for items that no longer exist
        
        Args:
            valid_item_ids: List of item IDs that still exist in the database
            
        Returns:
            Number of orphaned images cleaned up
        """
        cleaned_count = 0
        items_dir = self.base_path / "items"
        
        if not items_dir.exists():
            return 0
            
        for item_dir in items_dir.iterdir():
            if item_dir.is_dir() and item_dir.name not in valid_item_ids:
                try:
                    # Get all images for this orphaned item
                    images = self.get_item_images(item_dir.name)
                    
                    # Delete each image
                    for image_metadata in images:
                        if self.delete_image(image_metadata['image_id']):
                            cleaned_count += 1
                            
                    # Remove empty directory
                    if not any(item_dir.iterdir()):
                        item_dir.rmdir()
                        
                except Exception as e:
                    print(f"Error cleaning up orphaned images in {item_dir}: {str(e)}")
                    
        return cleaned_count
        
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        stats = {
            'total_images': 0,
            'total_size_bytes': 0,
            'items_with_images': 0,
            'thumbnail_count': 0
        }
        
        items_dir = self.base_path / "items"
        if items_dir.exists():
            for item_dir in items_dir.iterdir():
                if item_dir.is_dir():
                    images = self.get_item_images(item_dir.name)
                    if images:
                        stats['items_with_images'] += 1
                        stats['total_images'] += len(images)
                        
                        for image in images:
                            image_path = self.base_path / image['file_path']
                            if image_path.exists():
                                stats['total_size_bytes'] += image_path.stat().st_size
                                
        # Count thumbnails
        for thumb_dir in ['small', 'medium']:
            thumb_path = self.base_path / "thumbnails" / thumb_dir
            if thumb_path.exists():
                stats['thumbnail_count'] += len(list(thumb_path.glob("*.jpg")))
                
        return stats
