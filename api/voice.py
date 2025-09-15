"""
Voice API endpoints for BinBot - supports both browser and OpenAI voice
"""

import io
import base64
import logging
import re
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel

from config.settings import Settings
from llm.client import LLMClient

# Set up logger
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Request/Response models
class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    model: Optional[str] = None

class VoiceConfigResponse(BaseModel):
    provider: str
    available_voices: list
    current_settings: dict

# Initialize services
settings = Settings()
llm_client = None

def get_llm_client():
    global llm_client
    if llm_client is None:
        llm_client = LLMClient(settings.config)
        llm_client.initialize()  # Initialize the OpenAI client
    return llm_client

@router.get("/config", response_model=VoiceConfigResponse)
async def get_voice_config():
    """Get current voice configuration and available options"""
    try:
        voice_config = settings.get_voice_config()
        provider = voice_config.get('provider', 'browser')
        
        if provider == 'openai':
            available_voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
            current_settings = voice_config.get('openai', {})
        else:
            # Browser voices are determined client-side
            available_voices = ['browser-default']
            current_settings = voice_config.get('browser', {})
            
        return VoiceConfigResponse(
            provider=provider,
            available_voices=available_voices,
            current_settings=current_settings
        )
        
    except Exception as e:
        logger.error(f"Error getting voice config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get voice configuration")

@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech using configured provider"""
    try:
        voice_config = settings.get_voice_config()
        provider = voice_config.get('provider', 'browser')

        if provider == 'openai':
            return await _openai_tts(request, voice_config)
        else:
            # For browser TTS, we just return the text and let the frontend handle it
            return {
                "success": True,
                "provider": "browser",
                "text": request.text,
                "message": "Use browser TTS on frontend"
            }
            
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")

@router.post("/stt")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """Convert speech to text using configured provider"""
    try:
        voice_config = settings.get_voice_config()
        provider = voice_config.get('provider', 'browser')

        if provider == 'openai':
            return await _openai_stt(audio_file, voice_config)
        else:
            # For browser STT, this endpoint shouldn't be called
            return {
                "success": False,
                "provider": "browser",
                "message": "Browser STT is handled client-side"
            }
            
    except Exception as e:
        logger.error(f"Error in speech-to-text: {e}")
        raise HTTPException(status_code=500, detail=f"STT failed: {str(e)}")

async def _openai_tts(request: TTSRequest, voice_config: dict):
    """Handle OpenAI Text-to-Speech"""
    try:
        client = get_llm_client()
        openai_config = voice_config.get('openai', {})

        # Use request parameters or fall back to config defaults
        model = request.model or openai_config.get('tts_model', 'tts-1')
        voice = request.voice or openai_config.get('tts_voice', 'alloy')
        audio_format = openai_config.get('audio_format', 'opus')

        # Preprocess text for faster, cleaner speech
        text = _preprocess_text_for_speech(request.text)

        logger.info(f"OpenAI TTS: model={model}, voice={voice}, format={audio_format}, text_length={len(text)}")

        # Call OpenAI TTS API with streaming for faster response
        response = client.openai_client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format=audio_format,
            speed=1.0  # Normal speed, can be 0.25 to 4.0
        )

        # Convert audio to base64 for JSON response
        audio_data = response.content
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return {
            "success": True,
            "provider": "openai",
            "audio_data": audio_base64,
            "audio_format": audio_format,
            "model": model,
            "voice": voice,
            "text": request.text
        }
        
    except Exception as e:
        logger.error(f"OpenAI TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI TTS failed: {str(e)}")

async def _openai_stt(audio_file: UploadFile, voice_config: dict):
    """Handle OpenAI Speech-to-Text (Whisper)"""
    try:
        client = get_llm_client()
        openai_config = voice_config.get('openai', {})
        
        model = openai_config.get('whisper_model', 'whisper-1')
        
        logger.info(f"OpenAI STT: model={model}, file={audio_file.filename}")
        
        # Read audio file
        audio_data = await audio_file.read()
        
        # Create a file-like object for OpenAI API
        audio_file_obj = io.BytesIO(audio_data)
        audio_file_obj.name = audio_file.filename or "audio.wav"
        
        # Call OpenAI Whisper API
        response = await client.openai_client.audio.transcriptions.create(
            model=model,
            file=audio_file_obj
        )
        
        transcript = response.text
        
        return {
            "success": True,
            "provider": "openai",
            "transcript": transcript,
            "model": model,
            "confidence": 1.0  # OpenAI doesn't provide confidence scores
        }

    except Exception as e:
        logger.error(f"OpenAI STT error: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI STT failed: {str(e)}")

def _preprocess_text_for_speech(text: str) -> str:
    """Preprocess text for faster, cleaner speech synthesis"""
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())

    # Expand common abbreviations for better pronunciation
    abbreviations = {
        'bin': 'bin',  # Keep as is - sounds fine
        'qty': 'quantity',
        'desc': 'description',
        'loc': 'location',
        'id': 'I D',  # Spell out for clarity
        'api': 'A P I',
        'url': 'U R L',
        'http': 'H T T P',
        'https': 'H T T P S',
        'db': 'database',
        'config': 'configuration'
    }

    # Replace abbreviations (case insensitive, word boundaries)
    for abbr, expansion in abbreviations.items():
        pattern = r'\b' + re.escape(abbr) + r'\b'
        text = re.sub(pattern, expansion, text, flags=re.IGNORECASE)

    # Limit length for faster processing (OpenAI TTS has 4096 char limit)
    if len(text) > 500:  # Keep responses concise for speed
        text = text[:497] + "..."

    return text
