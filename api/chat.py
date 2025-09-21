"""
Chat endpoints for BinBot
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from pydantic import BaseModel
import tempfile
import os
from pathlib import Path
from api_schemas import ChatResponse, ImageUploadResponse, ItemInput
from llm.client import get_gemini_client
from chat.function_wrappers import get_function_wrappers, create_function_mapping
from session.session_manager import get_session_manager
from storage.image_storage import get_image_storage
from llm.vision import get_vision_service

router = APIRouter()


def create_function_mapping(wrappers):
    """Create mapping between function names and wrapper methods"""
    return {
        "add_items": wrappers.add_items,
        "search_items": wrappers.search_items,
        "get_bin_contents": wrappers.get_bin_contents,
        "move_items": wrappers.move_items,
        "remove_items": wrappers.remove_items
    }


class ChatCommandRequest(BaseModel):
    """Request for chat command (message only, session from cookie)"""
    message: str

@router.post("/api/chat/command", response_model=ChatResponse)
async def chat(chat_request: ChatCommandRequest, request: Request):
    """Chat with LLM using session-bound functions and automatic execution"""
    # Get session ID from cookie
    session_id = request.cookies.get('session_id')
    if not session_id:
        raise HTTPException(status_code=401, detail="No active session")

    # Get session manager and validate session
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    # Add user message to conversation
    session_manager.add_message(session_id, "user", chat_request.message)
    
    # Get conversation history
    conversation = session_manager.get_conversation(session_id)

    # Convert to LLM format
    messages = []
    for msg in conversation:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Create session-bound function wrappers
    wrappers = get_function_wrappers(session_id)
    function_mapping = create_function_mapping(wrappers)

    # Tools are now the actual Python functions (automatic function calling)
    tools = list(function_mapping.values())
    
    # Get LLM client and send chat
    llm_client = get_gemini_client()

    try:
        # Send to LLM with automatic function calling enabled
        response_text = llm_client.chat_completion(messages, tools)

        # Add model response to conversation
        session_manager.add_message(session_id, "model", response_text)

        return ChatResponse(success=True, response=response_text)

    except Exception as e:
        error_msg = f"Chat error: {str(e)}"
        session_manager.add_message(session_id, "model", error_msg)
        return ChatResponse(success=False, response=error_msg)


@router.post("/api/chat/image", response_model=ImageUploadResponse)
async def chat_image(
    file: UploadFile = File(...),
    request: Request = None
):
    """Upload image, analyze contents, and add to session context"""
    # Get session ID from cookie
    session_id = request.cookies.get('session_id')
    if not session_id:
        raise HTTPException(status_code=401, detail="No active session")
    
    # Validate session
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
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
        
        # Add image analysis to session context
        analysis_summary = f"Image uploaded and analyzed. Found {len(analyzed_items)} items: "
        analysis_summary += ", ".join([item.name for item in analyzed_items])
        session_manager.add_message(session_id, "user", f"[Image uploaded: {file.filename}]")
        session_manager.add_message(session_id, "model", analysis_summary)
        
        return ImageUploadResponse(
            success=True,
            image_id=image_id,
            analyzed_items=analyzed_items
        )
        
    except Exception as e:
        error_msg = f"Image analysis error: {str(e)}"
        session_manager.add_message(session_id, "model", error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except PermissionError:
                # On Windows, sometimes the file is still in use
                # Try again after a brief moment
                import time
                time.sleep(0.1)
                try:
                    os.unlink(temp_path)
                except PermissionError:
                    # If still can't delete, log it but don't fail
                    print(f"Warning: Could not delete temporary file {temp_path}")
