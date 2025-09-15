"""
Image Management API for BinBot

This module provides endpoints for image upload, processing, and management.
Supports image capture, storage, compression, and association with inventory items.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse
from api_schemas import StandardResponse, ErrorDetail, ImageMetadata, ImageUploadRequest
from database.chromadb_client import ChromaDBClient
from storage.image_storage import ImageStorage
from llm.vision import VisionService
from llm.embeddings import EmbeddingService
from typing import Optional, List
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


@router.post("/upload-to-bin", response_model=StandardResponse)
async def upload_image_to_bin(
    file: UploadFile = File(...),
    bin_id: str = Form(...),
    auto_analyze: bool = Form(True)
):
    """
    Upload an image to a bin and optionally auto-analyze to create items

    Args:
        file: Image file to upload
        bin_id: Bin ID to upload the image to
        auto_analyze: Whether to automatically analyze the image and create items
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

        # Read file data
        file_data = await file.read()

        # Create a temporary item ID for image storage (will be updated later)
        temp_item_id = f"temp_{uuid.uuid4()}"

        # Save image to storage
        image_metadata = image_storage.save_image(
            image_data=file_data,
            item_id=temp_item_id,
            bin_id=bin_id,
            filename=file.filename
        )

        result_data = {
            "message": "Image uploaded successfully",
            "image_id": image_metadata['image_id'],
            "bin_id": bin_id,
            "metadata": image_metadata,
            "items_created": []
        }

        # Auto-analyze if requested and vision service is available
        if auto_analyze and vision_service:
            try:
                # Get image path for analysis
                image_path = image_storage.get_image_path(image_metadata['image_id'], "full")

                if image_path:
                    # Analyze image to identify items
                    analysis_result = vision_service.identify_item(image_path, f"bin {bin_id}")

                    if analysis_result.get("success", False):
                        # Handle multiple items from analysis
                        items_data = analysis_result.get("items", [])

                        # Fallback for old single-item format
                        if not items_data and analysis_result.get("item_name"):
                            items_data = [{
                                "item_name": analysis_result.get("item_name"),
                                "description": analysis_result.get("description", "Item identified from image"),
                                "category": analysis_result.get("category", "unknown"),
                                "characteristics": analysis_result.get("characteristics", []),
                                "confidence": analysis_result.get("confidence", 5)
                            }]

                        if items_data:
                            # Create the items in the database
                            if embedding_service is None:
                                raise HTTPException(status_code=500, detail="Embedding service not initialized")

                            created_items = []
                            items_to_add = []

                            for item_info in items_data:
                                item_name = item_info.get("item_name", "Unknown Item")
                                description = item_info.get("description", "Item identified from image")
                                category = item_info.get("category", "unknown")
                                confidence = item_info.get("confidence", 5)

                                # Generate embedding for the item
                                embedding_text = f"{item_name} {description}"
                                embedding = embedding_service.generate_embedding(embedding_text)

                                # Debug logging
                                print(f"DEBUG IMAGE UPLOAD: Generated embedding for '{item_name}'")
                                print(f"DEBUG IMAGE UPLOAD: Embedding text: '{embedding_text}'")
                                print(f"DEBUG IMAGE UPLOAD: Embedding type: {type(embedding)}")
                                print(f"DEBUG IMAGE UPLOAD: Embedding length: {len(embedding) if embedding else 'None'}")
                                if embedding:
                                    print(f"DEBUG IMAGE UPLOAD: Embedding sample: {embedding[:5]}")

                                if embedding is not None:
                                    # Create item with proper metadata
                                    item_id = str(uuid.uuid4())
                                    item_data = {
                                        "id": item_id,
                                        "name": item_name,
                                        "description": description,
                                        "bin_id": bin_id,
                                        "embedding": embedding,
                                        "created_at": datetime.now().isoformat(),
                                        "updated_at": datetime.now().isoformat(),
                                        "images_count": 1,
                                        "images_json": image_metadata['image_id'],
                                        "primary_image": image_metadata['image_id'],
                                        "category": category,
                                        "confidence_score": confidence
                                    }

                                    items_to_add.append(item_data)
                                    created_items.append({
                                        "item_id": item_id,
                                        "name": item_name,
                                        "description": description,
                                        "category": category,
                                        "confidence": confidence
                                    })

                            # Add items to database individually (more reliable than bulk)
                            if items_to_add:
                                successfully_added = []
                                failed_items = []

                                for item_data in items_to_add:
                                    # Debug logging before add_document
                                    print(f"DEBUG IMAGE UPLOAD: About to add item '{item_data['name']}'")
                                    print(f"DEBUG IMAGE UPLOAD: Item embedding type: {type(item_data['embedding'])}")
                                    print(f"DEBUG IMAGE UPLOAD: Item embedding length: {len(item_data['embedding']) if item_data['embedding'] else 'None'}")
                                    if item_data['embedding']:
                                        print(f"DEBUG IMAGE UPLOAD: Item embedding sample: {item_data['embedding'][:5]}")

                                    # Use individual add_document method which we know works
                                    created_item_id = db_client.add_document(
                                        name=item_data["name"],
                                        bin_id=item_data["bin_id"],
                                        description=item_data["description"],
                                        embedding=item_data["embedding"]
                                    )

                                    if created_item_id:
                                        # Associate image with the newly created item using the actual ID
                                        image_success = db_client.add_image_to_item(
                                            item_id=created_item_id,
                                            image_id=image_metadata['image_id'],
                                            set_as_primary=True
                                        )

                                        if image_success:
                                            successfully_added.append(item_data)
                                            # Update image storage with the actual item ID
                                            image_storage.update_item_id(image_metadata['image_id'], temp_item_id, created_item_id)
                                        else:
                                            print(f"WARNING: Item created but failed to associate image for '{item_data['name']}'")
                                            successfully_added.append(item_data)
                                            # Still update image storage even if association failed
                                            image_storage.update_item_id(image_metadata['image_id'], temp_item_id, created_item_id)
                                    else:
                                        failed_items.append(item_data["name"])

                                if successfully_added:
                                    result_data["items_created"] = created_items[:len(successfully_added)]
                                    total_items = len(successfully_added)
                                    if total_items == 1:
                                        result_data["message"] = f"Image uploaded and 1 item created successfully"
                                    else:
                                        result_data["message"] = f"Image uploaded and {total_items} items created successfully"
                                    if failed_items:
                                        result_data["message"] += f" ({len(failed_items)} failed)"
                                    result_data["analysis"] = analysis_result
                                    if failed_items:
                                        result_data["failed_items"] = failed_items
                                else:
                                    result_data["analysis_error"] = f"Failed to create any items in database. Failed items: {failed_items}"
                            else:
                                result_data["analysis_error"] = "No valid items found in analysis or failed to generate embeddings"
                        else:
                            result_data["analysis_error"] = "No items identified in image"
                    else:
                        result_data["analysis_error"] = analysis_result.get("error", "Failed to analyze image")
                else:
                    result_data["analysis_error"] = "Image file not found after upload"

            except Exception as e:
                result_data["analysis_error"] = f"Auto-analysis failed: {str(e)}"

        return StandardResponse(
            success=True,
            data=result_data
        )

    except HTTPException:
        raise
    except Exception as e:
        error_detail = ErrorDetail(
            code="UPLOAD_ERROR",
            message=f"Failed to upload image to bin: {str(e)}",
            details={"bin_id": bin_id, "filename": file.filename if file else None}
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
        analysis_result = vision_service.identify_item(image_path, context)

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
        search_result = vision_service.search_by_image(image_path, query)

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


@router.post("/compare", response_model=StandardResponse)
async def compare_images(image_id1: str, image_id2: str):
    """
    Compare two images to determine if they show the same item

    Args:
        image_id1: First image ID
        image_id2: Second image ID
    """
    try:
        if not vision_service:
            error_detail = ErrorDetail(
                code="SERVICE_UNAVAILABLE",
                message="Vision service not available",
                details={"image_id1": image_id1, "image_id2": image_id2}
            )
            return StandardResponse(success=False, error=error_detail)

        if not image_storage:
            raise HTTPException(status_code=500, detail="Image storage not initialized")

        # Get both image file paths
        image_path1 = image_storage.get_image_path(image_id1, "full")
        image_path2 = image_storage.get_image_path(image_id2, "full")

        if not image_path1 or not os.path.exists(image_path1):
            error_detail = ErrorDetail(
                code="IMAGE_NOT_FOUND",
                message=f"Image {image_id1} not found",
                details={"image_id": image_id1}
            )
            return StandardResponse(success=False, error=error_detail)

        if not image_path2 or not os.path.exists(image_path2):
            error_detail = ErrorDetail(
                code="IMAGE_NOT_FOUND",
                message=f"Image {image_id2} not found",
                details={"image_id": image_id2}
            )
            return StandardResponse(success=False, error=error_detail)

        # Compare images
        comparison_result = vision_service.compare_items(image_path1, image_path2)

        if not comparison_result.get("success", False):
            error_detail = ErrorDetail(
                code="COMPARISON_ERROR",
                message=comparison_result.get("error", "Failed to compare images"),
                details={"image_id1": image_id1, "image_id2": image_id2}
            )
            return StandardResponse(success=False, error=error_detail)

        return StandardResponse(
            success=True,
            data={
                "image_id1": image_id1,
                "image_id2": image_id2,
                "comparison": comparison_result
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        error_detail = ErrorDetail(
            code="COMPARISON_ERROR",
            message=f"Failed to compare images: {str(e)}",
            details={"image_id1": image_id1, "image_id2": image_id2}
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
        description_result = vision_service.describe_for_accessibility(image_path)

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
