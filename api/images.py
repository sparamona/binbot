"""
Image management endpoints for BinBot
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
import tempfile
import os
from pathlib import Path
from api_schemas import ImageUploadResponse, ImageAnalysisRequest, ItemInput
from storage.image_storage import get_image_storage
from llm.vision import get_vision_service

router = APIRouter()


@router.post("/api/images", response_model=ImageUploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """Upload image, auto-analyze, and return structured items"""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name
    
    try:
        # Store image
        image_storage = get_image_storage()
        image_id = image_storage.save_image(temp_path, file.filename)
        
        # Analyze image for items
        vision_service = get_vision_service()
        analyzed_items_data = vision_service.analyze_image(temp_path)
        
        # Convert to ItemInput format
        analyzed_items = []
        for item_data in analyzed_items_data:
            item = ItemInput(
                name=item_data.get('name', ''),
                description=item_data.get('description', ''),
                image_id=image_id
            )
            analyzed_items.append(item)
        
        return ImageUploadResponse(
            success=True,
            image_id=image_id,
            analyzed_items=analyzed_items
        )
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post("/api/images/{image_id}/analyze", response_model=ImageUploadResponse)
async def analyze_image(image_id: str, request: ImageAnalysisRequest):
    """Re-analyze image"""
    image_storage = get_image_storage()
    
    # Check if image exists
    image_metadata = image_storage.get_image_metadata(image_id)
    if not image_metadata:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Get image path or data
    if hasattr(image_storage, 'get_image_data') and image_storage.get_image_data(image_id):
        # In-memory mode - need to create temporary file
        image_data = image_storage.get_image_data(image_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(image_data)
            temp_path = temp_file.name
        
        try:
            # Analyze image
            vision_service = get_vision_service()
            analyzed_items_data = vision_service.analyze_image(temp_path)
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    else:
        # File mode
        image_path = image_storage.get_image_path(image_id)
        if not image_path or not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image file not found")
        
        # Analyze image
        vision_service = get_vision_service()
        analyzed_items_data = vision_service.analyze_image(image_path)
    
    # Convert to ItemInput format
    analyzed_items = []
    for item_data in analyzed_items_data:
        item = ItemInput(
            name=item_data.get('name', ''),
            description=item_data.get('description', ''),
            image_id=image_id
        )
        analyzed_items.append(item)
    
    return ImageUploadResponse(
        success=True,
        image_id=image_id,
        analyzed_items=analyzed_items
    )


@router.get("/api/images/{image_id}")
async def get_image(image_id: str):
    """Serve stored image asset"""
    image_storage = get_image_storage()

    # Check if image exists
    image_metadata = image_storage.get_image_metadata(image_id)
    if not image_metadata:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Get image data
    if hasattr(image_storage, 'get_image_data') and image_storage.get_image_data(image_id):
        # In-memory mode
        image_data = image_storage.get_image_data(image_id)
        
        # Determine content type from filename
        filename = image_metadata.get('filename', '')
        if filename.lower().endswith('.png'):
            media_type = "image/png"
        elif filename.lower().endswith('.gif'):
            media_type = "image/gif"
        else:
            media_type = "image/jpeg"
        
        return Response(content=image_data, media_type=media_type)
    else:
        # File mode
        image_path = image_storage.get_image_path(image_id)
        if not image_path or not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image file not found")
        
        # Read file and return
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Determine content type from file extension
        path = Path(image_path)
        if path.suffix.lower() == '.png':
            media_type = "image/png"
        elif path.suffix.lower() == '.gif':
            media_type = "image/gif"
        else:
            media_type = "image/jpeg"
        
        return Response(content=image_data, media_type=media_type)
