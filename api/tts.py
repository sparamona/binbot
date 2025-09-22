"""
Text-to-Speech endpoints for BinBot using OpenAI TTS API
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import httpx
import asyncio
from typing import Literal

from config.settings import OPENAI_API_KEY
from utils.logging import setup_logger

# Set up logger for TTS endpoint
logger = setup_logger(__name__)

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = "alloy"
    model: Literal["tts-1", "tts-1-hd"] = "tts-1"


@router.post("/api/tts/speak")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech using OpenAI TTS API"""

    logger.info(f"TTS request: text='{request.text[:50]}...', voice={request.voice}, model={request.model}")

    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not configured")
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    if not request.text.strip():
        logger.error("Empty text provided for TTS")
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        logger.info("Calling OpenAI TTS API...")
        # Call OpenAI TTS API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": request.model,
                    "input": request.text,
                    "voice": request.voice,
                    "response_format": "mp3"
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                error_detail = f"OpenAI API error: {response.status_code}"
                try:
                    error_json = response.json()
                    error_detail = error_json.get("error", {}).get("message", error_detail)
                    logger.error(f"OpenAI API error response: {error_json}")
                except Exception as e:
                    logger.error(f"Failed to parse OpenAI error response: {e}")
                logger.error(f"OpenAI TTS API failed: {error_detail}")
                raise HTTPException(status_code=500, detail=error_detail)
            
            # Return audio data as MP3
            logger.info(f"TTS successful, returning {len(response.content)} bytes of audio")
            return Response(
                content=response.content,
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": "inline; filename=speech.mp3",
                    "Cache-Control": "no-cache"
                }
            )
            
    except httpx.TimeoutException:
        logger.error("OpenAI API timeout")
        raise HTTPException(status_code=504, detail="OpenAI API timeout")
    except httpx.RequestError as e:
        logger.error(f"HTTP request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected TTS error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
