"""
Image Management API for BinBot

This module provides endpoints for image upload, processing, and management.
Supports image capture, storage, compression, and association with inventory items.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from api_schemas import StandardResponse, ErrorDetail
from database.chromadb_client import ChromaDBClient
from storage.image_storage import ImageStorage
from llm.vision import VisionService
from llm.embeddings import EmbeddingService
from typing import Optional
import uuid
from datetime import datetime
import os

router = APIRouter(prefix="/images", tags=["images"])

# Global dependencies (will be set by main app)
db_client: ChromaDBClient = None
image_storage: ImageStorage = None
vision_service: VisionService = None
embedding_service: EmbeddingService = None


def set_dependencies(db: ChromaDBClient, storage: ImageStorage, vision: VisionService = None, embeddings: EmbeddingService = None):
    """Set dependencies for the images router"""
    global db_client, image_storage, vision_service, embedding_service
    db_client = db
    image_storage = storage
    vision_service = vision
    embedding_service = embeddings


@router.post("/upload", response_model=StandardResponse)
async def upload_image(
    file: UploadFile = File(...),
    item_id: str = Form(...),
    set_as_primary: bool = Form(False)
):
    """
    Upload an image and associate it with an inventory item
    
    Args:
        file: Image file to upload
        item_id: Item ID to associate the image with
        set_as_primary: Whether to set this as the primary image for the item
    """
    try:
        if not db_client or not image_storage:
            raise HTTPException(status_code=500, detail="Services not initialized")
            
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            error_detail = ErrorDetail(
                code="INVALID_FILE_TYPE",
                message="File must be an image",
                details={"content_type": file.content_type}
            )
            return StandardResponse(success=False, error=error_detail)
            
        # Check if item exists
        item_result = db_client.inventory_collection.get(
            ids=[item_id],
            include=['metadatas']
        )
        
        if not item_result['ids'] or len(item_result['ids']) == 0:
            error_detail = ErrorDetail(
                code="ITEM_NOT_FOUND",
                message=f"Item {item_id} not found",
                details={"item_id": item_id}
            )
            return StandardResponse(success=False, error=error_detail)
            
        item_metadata = item_result['metadatas'][0]
        bin_id = item_metadata.get('bin_id', '')
        
        # Read file data
        file_data = await file.read()
        
        # Save image to storage
        image_metadata = image_storage.save_image(
            image_data=file_data,
            item_id=item_id,
            bin_id=bin_id,
            filename=file.filename
        )
        
        # Associate image with item in database
        success = db_client.add_image_to_item(
            item_id=item_id,
            image_id=image_metadata['image_id'],
            set_as_primary=set_as_primary
        )
        
        if not success:
            # Clean up saved image if database update failed
            image_storage.delete_image(image_metadata['image_id'])
            raise HTTPException(status_code=500, detail="Failed to associate image with item")
            
        return StandardResponse(
            success=True,
            data={
                "message": "Image uploaded successfully",
                "image_id": image_metadata['image_id'],
                "item_id": item_id,
                "set_as_primary": set_as_primary,
                "metadata": image_metadata
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = ErrorDetail(
            code="UPLOAD_ERROR",
            message=f"Failed to upload image: {str(e)}",
            details={"item_id": item_id, "filename": file.filename if file else None}
        )
        return StandardResponse(success=False, error=error_detail)






@router.get("/item/{item_id}", response_model=StandardResponse)
async def get_item_images(item_id: str):
    """Get all images associated with an item"""
    try:
        if not db_client or not image_storage:
            raise HTTPException(status_code=500, detail="Services not initialized")

        # Get item from database to access image metadata
        result = db_client.inventory_collection.get(
            ids=[item_id],
            include=['metadatas']
        )

        if not result['ids'] or len(result['ids']) == 0:
            error_detail = ErrorDetail(
                code="ITEM_NOT_FOUND",
                message=f"Item {item_id} not found",
                details={"item_id": item_id}
            )
            return StandardResponse(success=False, error=error_detail)

        metadata = result['metadatas'][0]

        # Parse images from ChromaDB format
        images_json = metadata.get('images_json', '')
        image_ids = images_json.split(',') if images_json else []
        image_ids = [img.strip() for img in image_ids if img.strip()]  # Clean up

        primary_image = metadata.get('primary_image', '')

        # Build image objects with metadata
        images = []
        for image_id in image_ids:
            try:
                image_metadata = image_storage.get_image_metadata(image_id)
                if image_metadata:
                    images.append({
                        "image_id": image_id,
                        "metadata": image_metadata,
                        "is_primary": image_id == primary_image
                    })
            except Exception as e:
                print(f"Warning: Could not get metadata for image {image_id}: {e}")
                # Still include the image even if metadata is missing
                images.append({
                    "image_id": image_id,
                    "metadata": None,
                    "is_primary": image_id == primary_image
                })

        return StandardResponse(
            success=True,
            data={
                "item_id": item_id,
                "images": images,
                "primary_image": primary_image,
                "count": len(images)
            }
        )

    except Exception as e:
        error_detail = ErrorDetail(
            code="FETCH_ERROR",
            message=f"Failed to get images for item: {str(e)}",
            details={"item_id": item_id}
        )
        return StandardResponse(success=False, error=error_detail)


@router.get("/metadata/{image_id}", response_model=StandardResponse)
async def get_image_metadata(image_id: str):
    """Get metadata for a specific image"""
    try:
        if not image_storage:
            raise HTTPException(status_code=500, detail="Image storage not initialized")
            
        metadata = image_storage.get_image_metadata(image_id)
        
        if not metadata:
            error_detail = ErrorDetail(
                code="IMAGE_NOT_FOUND",
                message=f"Image {image_id} not found",
                details={"image_id": image_id}
            )
            return StandardResponse(success=False, error=error_detail)
            
        return StandardResponse(
            success=True,
            data=metadata
        )
        
    except Exception as e:
        error_detail = ErrorDetail(
            code="FETCH_ERROR",
            message=f"Failed to get image metadata: {str(e)}",
            details={"image_id": image_id}
        )
        return StandardResponse(success=False, error=error_detail)


@router.get("/file/{image_id}")
async def get_image_file(image_id: str, size: str = "full"):
    """
    Get image file by ID
    
    Args:
        image_id: Image ID
        size: Image size - "full", "medium", or "small"
    """
    try:
        if not image_storage:
            raise HTTPException(status_code=500, detail="Image storage not initialized")
            
        if size not in ["full", "medium", "small"]:
            raise HTTPException(status_code=400, detail="Size must be 'full', 'medium', or 'small'")
            
        file_path = image_storage.get_image_path(image_id, size)
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image not found")
            
        return FileResponse(
            path=file_path,
            media_type="image/jpeg",
            filename=f"{image_id}_{size}.jpg"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve image: {str(e)}")


@router.delete("/{image_id}", response_model=StandardResponse)
async def delete_image(image_id: str):
    """Delete an image and remove it from associated item"""
    try:
        if not db_client or not image_storage:
            raise HTTPException(status_code=500, detail="Services not initialized")
            
        # Get image metadata to find associated item
        metadata = image_storage.get_image_metadata(image_id)
        
        if not metadata:
            error_detail = ErrorDetail(
                code="IMAGE_NOT_FOUND",
                message=f"Image {image_id} not found",
                details={"image_id": image_id}
            )
            return StandardResponse(success=False, error=error_detail)
            
        item_id = metadata['item_id']
        
        # Remove image from item in database
        db_success = db_client.remove_image_from_item(item_id, image_id)
        
        # Delete image files from storage
        storage_success = image_storage.delete_image(image_id)
        
        if not db_success or not storage_success:
            error_detail = ErrorDetail(
                code="DELETE_ERROR",
                message="Failed to completely delete image",
                details={
                    "image_id": image_id,
                    "database_success": db_success,
                    "storage_success": storage_success
                }
            )
            return StandardResponse(success=False, error=error_detail)
            
        return StandardResponse(
            success=True,
            data={
                "message": "Image deleted successfully",
                "image_id": image_id,
                "item_id": item_id
            }
        )
        
    except Exception as e:
        error_detail = ErrorDetail(
            code="DELETE_ERROR",
            message=f"Failed to delete image: {str(e)}",
            details={"image_id": image_id}
        )
        return StandardResponse(success=False, error=error_detail)


@router.post("/{image_id}/set-primary", response_model=StandardResponse)
async def set_primary_image(image_id: str):
    """Set an image as the primary image for its associated item"""
    try:
        if not db_client or not image_storage:
            raise HTTPException(status_code=500, detail="Services not initialized")
            
        # Get image metadata to find associated item
        metadata = image_storage.get_image_metadata(image_id)
        
        if not metadata:
            error_detail = ErrorDetail(
                code="IMAGE_NOT_FOUND",
                message=f"Image {image_id} not found",
                details={"image_id": image_id}
            )
            return StandardResponse(success=False, error=error_detail)
            
        item_id = metadata['item_id']
        
        # Update item to set this image as primary
        success = db_client.add_image_to_item(
            item_id=item_id,
            image_id=image_id,
            set_as_primary=True
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to set primary image")
            
        return StandardResponse(
            success=True,
            data={
                "message": "Primary image set successfully",
                "image_id": image_id,
                "item_id": item_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = ErrorDetail(
            code="UPDATE_ERROR",
            message=f"Failed to set primary image: {str(e)}",
            details={"image_id": image_id}
        )
        return StandardResponse(success=False, error=error_detail)


@router.get("/stats", response_model=StandardResponse)
async def get_image_stats():
    """Get image storage statistics"""
    try:
        if not image_storage:
            raise HTTPException(status_code=500, detail="Image storage not initialized")
            
        stats = image_storage.get_storage_stats()
        
        return StandardResponse(
            success=True,
            data=stats
        )
        
    except Exception as e:
        error_detail = ErrorDetail(
            code="STATS_ERROR",
            message=f"Failed to get image statistics: {str(e)}"
        )
        return StandardResponse(success=False, error=error_detail)


@router.post("/analyze/{image_id}", response_model=StandardResponse)
async def analyze_image(image_id: str, context: Optional[str] = None):
    """
    Analyze an image using OpenAI Vision API to identify the item

    Args:
        image_id: Image ID to analyze
        context: Optional context about the item location
    """
    try:
        if not vision_service:
            error_detail = ErrorDetail(
                code="SERVICE_UNAVAILABLE",
                message="Vision service not available",
                details={"image_id": image_id}
            )
            return StandardResponse(success=False, error=error_detail)

        if not image_storage:
            raise HTTPException(status_code=500, detail="Image storage not initialized")

        # Get image file path
        image_path = image_storage.get_image_path(image_id, "full")

        if not image_path or not os.path.exists(image_path):
            error_detail = ErrorDetail(
                code="IMAGE_NOT_FOUND",
                message=f"Image {image_id} not found",
                details={"image_id": image_id}
            )
            return StandardResponse(success=False, error=error_detail)

        # Get image metadata for context
        metadata = image_storage.get_image_metadata(image_id)
        if metadata and not context:
            context = f"bin {metadata['bin_id']}"

        # Analyze image
        analysis_result = await vision_service.identify_item(image_path, context)

        if not analysis_result.get("success", False):
            error_detail = ErrorDetail(
                code="ANALYSIS_ERROR",
                message=analysis_result.get("error", "Failed to analyze image"),
                details={"image_id": image_id}
            )
            return StandardResponse(success=False, error=error_detail)

        return StandardResponse(
            success=True,
            data={
                "image_id": image_id,
                "analysis": analysis_result,
                "context": context
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        error_detail = ErrorDetail(
            code="ANALYSIS_ERROR",
            message=f"Failed to analyze image: {str(e)}",
            details={"image_id": image_id}
        )
        return StandardResponse(success=False, error=error_detail)


@router.post("/search-by-image/{image_id}", response_model=StandardResponse)
async def search_by_image(image_id: str, query: Optional[str] = None):
    """
    Generate search terms based on image content using Vision API

    Args:
        image_id: Image ID to analyze for search terms
        query: Optional additional search context
    """
    try:
        if not vision_service:
            error_detail = ErrorDetail(
                code="SERVICE_UNAVAILABLE",
                message="Vision service not available",
                details={"image_id": image_id}
            )
            return StandardResponse(success=False, error=error_detail)

        if not image_storage:
            raise HTTPException(status_code=500, detail="Image storage not initialized")

        # Get image file path
        image_path = image_storage.get_image_path(image_id, "full")

        if not image_path or not os.path.exists(image_path):
            error_detail = ErrorDetail(
                code="IMAGE_NOT_FOUND",
                message=f"Image {image_id} not found",
                details={"image_id": image_id}
            )
            return StandardResponse(success=False, error=error_detail)

        # Generate search terms
        search_result = await vision_service.search_by_image(image_path, query)

        if not search_result.get("success", False):
            error_detail = ErrorDetail(
                code="SEARCH_ERROR",
                message=search_result.get("error", "Failed to generate search terms"),
                details={"image_id": image_id}
            )
            return StandardResponse(success=False, error=error_detail)

        return StandardResponse(
            success=True,
            data={
                "image_id": image_id,
                "search_terms": search_result,
                "query": query
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        error_detail = ErrorDetail(
            code="SEARCH_ERROR",
            message=f"Failed to search by image: {str(e)}",
            details={"image_id": image_id}
        )
        return StandardResponse(success=False, error=error_detail)


@router.get("/describe/{image_id}", response_model=StandardResponse)
async def describe_image_for_accessibility(image_id: str):
    """
    Generate detailed description for accessibility/screen readers

    Args:
        image_id: Image ID to describe
    """
    try:
        if not vision_service:
            error_detail = ErrorDetail(
                code="SERVICE_UNAVAILABLE",
                message="Vision service not available",
                details={"image_id": image_id}
            )
            return StandardResponse(success=False, error=error_detail)

        if not image_storage:
            raise HTTPException(status_code=500, detail="Image storage not initialized")

        # Get image file path
        image_path = image_storage.get_image_path(image_id, "full")

        if not image_path or not os.path.exists(image_path):
            error_detail = ErrorDetail(
                code="IMAGE_NOT_FOUND",
                message=f"Image {image_id} not found",
                details={"image_id": image_id}
            )
            return StandardResponse(success=False, error=error_detail)

        # Generate description
        description_result = await vision_service.describe_for_accessibility(image_path)

        if not description_result.get("success", False):
            error_detail = ErrorDetail(
                code="DESCRIPTION_ERROR",
                message=description_result.get("error", "Failed to generate description"),
                details={"image_id": image_id}
            )
            return StandardResponse(success=False, error=error_detail)

        return StandardResponse(
            success=True,
            data={
                "image_id": image_id,
                "description": description_result.get("description", "")
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        error_detail = ErrorDetail(
            code="DESCRIPTION_ERROR",
            message=f"Failed to describe image: {str(e)}",
            details={"image_id": image_id}
        )
        return StandardResponse(success=False, error=error_detail)


