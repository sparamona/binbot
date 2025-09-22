"""
Chat endpoints for BinBot
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Query
from pydantic import BaseModel
from typing import Literal, Optional
import tempfile
import os
from pathlib import Path
from api_schemas import ChatResponse, ImageUploadResponse, ItemInput
from llm.client import get_gemini_client
from chat.function_wrappers import get_function_wrappers, create_function_mapping
from session.session_manager import get_session_manager
from storage.image_storage import get_image_storage
from llm.vision import get_vision_service
from utils.logging import setup_logger

# Set up logger for chat endpoint
logger = setup_logger(__name__)

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
    fmt: Optional[Literal["MD", "TTS"]] = "MD"

@router.post("/api/chat/command", response_model=ChatResponse)
async def chat(
    chat_request: ChatCommandRequest,
    request: Request,
    fmt: Optional[Literal["MD", "TTS"]] = Query("MD", description="Response format: MD for markdown, TTS for text-to-speech")
):
    """Chat with LLM using session-bound functions and automatic execution"""
    # Log request details for debugging
    logger.info(f"CHAT_REQUEST: {request.method} {request.url} - Query params: {dict(request.query_params)} - Body fmt: {chat_request.fmt}")

    # Get session ID from cookie
    session_id = request.cookies.get('session_id')
    if not session_id:
        raise HTTPException(status_code=401, detail="No active session")

    # Get session manager and validate session
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    # Use format from query parameter if provided, otherwise from request body
    response_format = fmt or chat_request.fmt

    # Add user message to conversation with format-specific instructions
    base_instructions = "\n\n The contents of any bin change at any time without your knowledge.  Remember to abide by system instructions.  Always use the tools provided whenever possible.  Never rely on your memory for bin contents.  ALWAYS use get_bin_contents to retrieve the contents of a bin."

    if response_format == "TTS":
        format_instructions = "\nRespond in a conversational, natural way suitable for text-to-speech. Keep responses short and avoid markdown formatting."
    else:
        format_instructions = ""  # No special instructions for MD format

    full_message = chat_request.message + base_instructions + format_instructions
    session_manager.add_message(session_id, "user", full_message)
    
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
        response_text = llm_client.chat_completion(messages, tools, response_format)

        # Add model response to conversation
        session_manager.add_message(session_id, "model", response_text)

        # Get current bin from session after function calls may have updated it
        updated_session = session_manager.get_session(session_id)
        current_bin = updated_session.get('current_bin') if updated_session else None

        logger.info(f"CHAT_RESPONSE: {session_id[:8]}... returning current_bin='{current_bin}'")
        return ChatResponse(success=True, response=response_text, current_bin=current_bin)

    except Exception as e:
        error_msg = f"Chat error: {str(e)}"
        session_manager.add_message(session_id, "model", error_msg)

        # Still include current_bin even on error
        session = session_manager.get_session(session_id)
        current_bin = session.get('current_bin') if session else None

        return ChatResponse(success=False, response=error_msg, current_bin=current_bin)


@router.post("/api/chat/image", response_model=ImageUploadResponse)
async def chat_image(
    request: Request,
    file: UploadFile = File(...),
    fmt: Optional[Literal["MD", "TTS"]] = Query("MD", description="Response format: MD for markdown, TTS for text-to-speech")
):
    """Upload image, analyze contents, and add to session context"""
    # Log request details for debugging
    logger.info(f"IMAGE_REQUEST: {request.method} {request.url} - Query params: {dict(request.query_params)} - File: {file.filename}")

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
        print(f"📁 Storing image: {file.filename}")
        image_storage = get_image_storage()
        image_id = image_storage.save_image(temp_path, file.filename)
        print(f"✅ Image stored with ID: {image_id}")

        # Analyze image for items
        print(f"👁️ Analyzing image with vision service...")
        vision_service = get_vision_service()
        analyzed_items_data = vision_service.analyze_image(temp_path)
        print(f"✅ Vision analysis complete: {len(analyzed_items_data)} items found")
        
        # Convert to ItemInput format
        analyzed_items = []
        for item_data in analyzed_items_data:
            item = ItemInput(
                name=item_data.get('name', ''),
                description=item_data.get('description', ''),
                image_id=image_id
            )
            analyzed_items.append(item)
        
        # Add image analysis to session context with proper image UUID and full details
        analysis_summary = f"Image uploaded and analyzed (image_id: {image_id}). Found {len(analyzed_items)} items:\n"
        for item in analyzed_items:
            analysis_summary += f"- Name: '{item.name}', Description: '{item.description}', Image ID: '{image_id}'\n"

        analysis_summary += f"\nWhen adding these items to a bin, use the exact image_id '{image_id}' and include both name and description for each item."

        session_manager.add_message(session_id, "user", f"[Image uploaded: {file.filename}]")
        session_manager.add_message(session_id, "model", analysis_summary)

        # Generate format-appropriate conversational response
        if fmt == "TTS":
            # Short, conversational response for TTS
            if len(analyzed_items) == 0:
                conversational_response = "I analyzed the image but didn't find any recognizable items."
            elif len(analyzed_items) == 1:
                item = analyzed_items[0]
                conversational_response = f"I found one item in the image: {item.name}."
            else:
                item_names = [item.name for item in analyzed_items]
                if len(item_names) <= 3:
                    items_text = ", ".join(item_names[:-1]) + f" and {item_names[-1]}"
                else:
                    items_text = f"{', '.join(item_names[:2])} and {len(item_names)-2} other items"
                conversational_response = f"I found {len(analyzed_items)} items in the image: {items_text}."
        else:
            # Rich markdown response for MD format
            if len(analyzed_items) == 0:
                conversational_response = "## 📷 Image Analysis Complete\n\n**No items found** in the uploaded image."
            else:
                conversational_response = f"## 📷 Image Analysis Complete\n\n**Found {len(analyzed_items)} item{'s' if len(analyzed_items) != 1 else ''}:**\n\n"
                for item in analyzed_items:
                    conversational_response += f"- **{item.name}**: {item.description}\n"
                conversational_response += f"\n*Ready to add to inventory when you specify a bin.*"

        return ImageUploadResponse(
            success=True,
            image_id=image_id,
            analyzed_items=analyzed_items,
            response=conversational_response
        )
        
    except Exception as e:
        error_msg = f"Image analysis error: {str(e)}"
        print(f"❌ Image upload error: {error_msg}")
        import traceback
        traceback.print_exc()
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
