"""
Natural Language Processing API for BinBot

This module provides endpoints for natural language inventory commands.
Users can interact with the system using plain English commands like:
- "add bolts to bin 3"
- "also add nuts"
- "remove wires from bin 2"
- "search for electronics"
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from api_schemas import StandardResponse, ErrorDetail
from nlp.function_command_processor import FunctionCommandProcessor

# Global dependencies (will be set by main app)
db_client = None
embedding_service = None
llm_client = None
vision_service = None
image_storage = None

def set_dependencies(db, embedding, llm=None, vision=None, storage=None):
    """Set the database, embedding service, LLM client, vision service, and image storage dependencies"""
    global db_client, embedding_service, llm_client, vision_service, image_storage
    db_client = db
    embedding_service = embedding
    llm_client = llm
    vision_service = vision
    image_storage = storage

router = APIRouter(prefix="/nlp", tags=["Natural Language Processing"])

class NLPCommandRequest(BaseModel):
    """Request model for natural language commands"""
    command: str
    session_id: Optional[str] = None



@router.post("/command", response_model=StandardResponse)
async def process_natural_language_command(request: NLPCommandRequest):
    """
    Process a natural language inventory command
    
    Examples:
    - "add bolts to bin 3"
    - "also add nuts" (uses context from previous command)
    - "remove wires from bin 2"
    - "move screws from bin 1 to bin 5"
    - "search for electronics"
    - "what's in bin 7?"
    """
    try:
        if not db_client or not embedding_service or not llm_client:
            raise HTTPException(status_code=500, detail="Service dependencies not initialized")

        if not request.command.strip():
            error_detail = ErrorDetail(
                code="EMPTY_COMMAND",
                message="Command cannot be empty",
                details={"command": request.command}
            )
            return StandardResponse(success=False, error=error_detail)

        # Initialize function-based command processor
        processor = FunctionCommandProcessor(
            db_client=db_client,
            embedding_service=embedding_service,
            llm_client=llm_client,
            vision_service=vision_service,
            image_storage=image_storage
        )
        
        # Process the command
        result = await processor.process_command(
            command_text=request.command,
            session_id=request.session_id
        )
        
        # Format response
        response_data = {
            "message": result.message,
            "command_processed": request.command,
            "timestamp": datetime.now().isoformat()
        }
        
        if result.data:
            response_data.update(result.data)
        
        if result.success:
            return StandardResponse(
                success=True,
                data=response_data
            )
        else:
            error_detail = ErrorDetail(
                code="COMMAND_FAILED",
                message=result.message,
                details={
                    "command": request.command,
                    "error": result.error,
                    "suggestions": getattr(result, 'suggestions', None)
                }
            )
            return StandardResponse(success=False, error=error_detail)
    
    except Exception as e:
        error_detail = ErrorDetail(
            code="PROCESSING_ERROR",
            message=f"Failed to process command: {str(e)}",
            details={"command": request.command, "error": str(e)}
        )
        return StandardResponse(success=False, error=error_detail)




@router.post("/command-with-image", response_model=StandardResponse)
async def process_command_with_image(
    command: str = Form(...),
    session_id: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None)
):
    """
    Process a natural language command with an optional image in a single call.

    - If an image is provided, it is analyzed inline and a concise text description
      is added to the conversation context before processing the command.
    - No long-term image association is created here; images are stored temporarily
      under a temp item context. Promotion to permanent storage can occur later
      if items are added from this command flow.
    """
    try:
        if not db_client or not embedding_service or not llm_client:
            raise HTTPException(status_code=500, detail="Service dependencies not initialized")

        # Build image context if an image is provided
        image_context = None
        if image is not None:
            if not image.content_type or not image.content_type.startswith('image/'):
                error_detail = ErrorDetail(
                    code="INVALID_FILE_TYPE",
                    message="File must be an image",
                    details={"content_type": image.content_type}
                )
                return StandardResponse(success=False, error=error_detail)

            file_content = await image.read()
            if len(file_content) > 10 * 1024 * 1024:  # 10MB limit
                error_detail = ErrorDetail(
                    code="FILE_TOO_LARGE",
                    message="File size must be less than 10MB",
                    details={"size": len(file_content)}
                )
                return StandardResponse(success=False, error=error_detail)

            if not image_storage or not vision_service:
                error_detail = ErrorDetail(
                    code="SERVICE_UNAVAILABLE",
                    message="Image analysis services not available"
                )
                return StandardResponse(success=False, error=error_detail)

            # Save image temporarily for analysis (temp item/bin context)
            temp_item_id = str(uuid.uuid4())
            try:
                image_metadata = image_storage.save_image(
                    image_data=file_content,
                    item_id=temp_item_id,
                    bin_id="temp",
                    filename=image.filename
                )
                actual_image_id = image_metadata.get("image_id") if image_metadata else None
                if not actual_image_id:
                    error_detail = ErrorDetail(
                        code="STORAGE_ERROR",
                        message="Failed to store image temporarily"
                    )
                    return StandardResponse(success=False, error=error_detail)

                image_path = image_storage.get_image_path(actual_image_id, "full")

                # Analyze the image once and create conversational analysis text
                analysis_result = vision_service.identify_item(image_path, "conversation")

                identified_items = []
                if analysis_result and analysis_result.get("success") and analysis_result.get("items"):
                    for item in analysis_result["items"]:
                        identified_items.append({
                            "name": item.get('item_name', 'Unknown item'),
                            "description": item.get('description', ''),
                            "confidence": item.get('confidence', 0.0)
                        })

                # Friendly analysis text
                if identified_items:
                    item_names = [item['name'] for item in identified_items]
                    if len(item_names) == 1:
                        analysis_text = f"🔍 I can see a {item_names[0]} in this image."
                    elif len(item_names) == 2:
                        analysis_text = f"🔍 I can see a {item_names[0]} and a {item_names[1]} in this image."
                    else:
                        items_list = ", ".join(item_names[:-1]) + f", and a {item_names[-1]}"
                        analysis_text = f"🔍 I can see a {items_list} in this image."
                else:
                    analysis_text = "🔍 I can see this image, but I'm having trouble identifying specific items."

                image_context = {
                    "image_id": actual_image_id,
                    "analysis": analysis_text,
                    "identified_items": identified_items
                }
            except Exception as e:
                error_detail = ErrorDetail(
                    code="ANALYSIS_ERROR",
                    message=f"Failed to analyze image: {str(e)}"
                )
                return StandardResponse(success=False, error=error_detail)

        # Initialize function-based command processor
        processor = FunctionCommandProcessor(
            db_client=db_client,
            embedding_service=embedding_service,
            llm_client=llm_client,
            vision_service=vision_service,
            image_storage=image_storage
        )

        # Process command immediately with optional image context
        result = await processor.process_command(
            command_text=command,
            session_id=session_id,
            image_context=image_context
        )

        # Format response
        response_data = {
            "response": result.message,
            "message": result.message,  # keep both keys for UI compatibility
            "command_processed": command,
            "timestamp": datetime.now().isoformat()
        }
        if image_context:
            response_data.update({
                "image_id": image_context.get("image_id"),
                "identified_items": image_context.get("identified_items", []),
                "analysis": image_context.get("analysis")
            })
        if result.data:
            response_data.update(result.data)

        if result.success:
            return StandardResponse(success=True, data=response_data)
        else:
            error_detail = ErrorDetail(
                code="COMMAND_FAILED",
                message=result.message,
                details={"command": command, "error": result.error}
            )
            return StandardResponse(success=False, error=error_detail)

    except HTTPException:
        raise
    except Exception as e:
        error_detail = ErrorDetail(
            code="PROCESSING_ERROR",
            message=f"Failed to process command with image: {str(e)}"
        )
        return StandardResponse(success=False, error=error_detail)


@router.get("/help", response_model=StandardResponse)
async def get_nlp_help():
    """Get help information for natural language commands"""
    
    help_data = {
        "title": "BinBot Natural Language Commands",
        "description": "You can interact with your inventory using plain English commands",
        "examples": [
            {
                "category": "Adding Items",
                "commands": [
                    "add bolts to bin 3",
                    "put screws in bin 5",
                    "place resistors in bin 7",
                    "also add nuts (uses previous bin)"
                ]
            },
            {
                "category": "Removing Items", 
                "commands": [
                    "remove wires from bin 2",
                    "take out capacitors from bin 4",
                    "delete old parts from bin 1"
                ]
            },
            {
                "category": "Moving Items",
                "commands": [
                    "move screws from bin 1 to bin 5",
                    "transfer tools from bin 3 to bin 8"
                ]
            },
            {
                "category": "Searching",
                "commands": [
                    "search for electronics",
                    "find tools",
                    "look for resistors"
                ]
            },
            {
                "category": "Listing Contents",
                "commands": [
                    "what's in bin 3?",
                    "show bin 7",
                    "list bin 2"
                ]
            },
            {
                "category": "Other",
                "commands": [
                    "help - show this help",
                    "undo - undo last command (coming soon)"
                ]
            }
        ],
        "tips": [
            "Commands are case-insensitive",
            "You can use follow-up commands like 'also add nuts' after specifying a bin",
            "The system remembers context from your previous commands",
            "If a command isn't understood, try rephrasing it",
            "Use specific item names for better results"
        ]
    }
    
    return StandardResponse(
        success=True,
        data=help_data
    )

@router.get("/examples", response_model=StandardResponse)
async def get_command_examples():
    """Get example commands for testing the natural language interface"""
    
    examples = {
        "basic_commands": [
            "add bolts to bin 3",
            "remove wires from bin 2", 
            "move screws from bin 1 to bin 5",
            "search for electronics",
            "what's in bin 7?"
        ],
        "context_commands": [
            "add resistors to bin 4",
            "also add capacitors",
            "and add LEDs"
        ],
        "complex_commands": [
            "add 5 screws and 3 bolts to bin 2",
            "move all tools from bin 1 to bin 8",
            "search for electronic components"
        ],
        "help_commands": [
            "help",
            "what can you do?",
            "show me commands"
        ]
    }
    
    return StandardResponse(
        success=True,
        data=examples
    )

@router.post("/test", response_model=StandardResponse)
async def test_command_parsing(request: NLPCommandRequest):
    """
    Test command parsing without executing the command
    
    This endpoint parses the command and returns what it understood
    without actually performing any inventory operations.
    """
    try:
        if not db_client or not embedding_service:
            raise HTTPException(status_code=500, detail="Service dependencies not initialized")
        
        # Initialize command processor
        processor = CommandProcessor(
            db_client=db_client,
            embedding_service=embedding_service,
            session_manager=session_manager
        )
        
        # Parse the command without executing
        parsed_command = processor.parser.parse_command(request.command)
        
        # Format parsing results
        parsing_result = {
            "original_command": request.command,
            "parsed_command_type": parsed_command.command_type.value,
            "items": parsed_command.items,
            "source_bin": parsed_command.source_bin,
            "target_bin": parsed_command.target_bin,
            "search_query": parsed_command.search_query,
            "confidence": parsed_command.confidence,
            "context_used": parsed_command.context_used,
            "interpretation": f"I understand this as: {parsed_command.command_type.value}"
        }
        
        if parsed_command.items:
            parsing_result["interpretation"] += f" items: {', '.join(parsed_command.items)}"
        
        if parsed_command.target_bin:
            parsing_result["interpretation"] += f" to bin {parsed_command.target_bin}"
        elif parsed_command.source_bin:
            parsing_result["interpretation"] += f" from bin {parsed_command.source_bin}"
        
        if parsed_command.search_query:
            parsing_result["interpretation"] += f" for: {parsed_command.search_query}"
        
        return StandardResponse(
            success=True,
            data=parsing_result
        )
    
    except Exception as e:
        error_detail = ErrorDetail(
            code="PARSING_ERROR",
            message=f"Failed to parse command: {str(e)}",
            details={"command": request.command, "error": str(e)}
        )
        return StandardResponse(success=False, error=error_detail)
