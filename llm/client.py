"""
Simple Gemini LLM client for BinBot using new google-genai SDK
"""

from google import genai
from google.genai import types
from typing import List, Dict, Any

from config.settings import GEMINI_API_KEY
from llm.prompts import SYSTEM_INSTRUCTIONS, TTS_SYSTEM_INSTRUCTIONS

# Model configuration
GEMINI_MODEL = "gemini-2.5-flash-lite"


class GeminiClient:
    """Simple Gemini LLM client using new google-genai SDK"""

    def __init__(self):
        pass

    def _create_client(self) -> genai.Client:
        """Create a fresh Gemini client for each request"""
        return genai.Client(api_key=GEMINI_API_KEY)

    def chat_completion(self, messages: List[Dict[str, str]], tools: List = None, format_type: str = "MD") -> str:
        """Send messages to Gemini and get response with automatic function calling using new SDK"""
        # Create fresh client for this request
        client = self._create_client()

        # Choose system instructions based on format type
        system_instructions = TTS_SYSTEM_INSTRUCTIONS if format_type == "TTS" else SYSTEM_INSTRUCTIONS

        # Separate the last message (current prompt) from history
        if not messages:
            return ""

        current_message = messages[-1]['content']
        history = messages[:-1] if len(messages) > 1 else []

        # Convert history to Gemini format
        history_contents = []
        for msg in history:
            history_contents.append(types.Content(
                role=msg['role'],
                parts=[types.Part(text=msg['content'])]
            ))

        # For now, let's go back to the working generate_content approach
        # Add current message to history for complete context
        all_contents = history_contents + [types.Content(
            role="user",
            parts=[types.Part(text=current_message)]
        )]

        if tools:
            # Configure automatic function calling with Python functions
            config = types.GenerateContentConfig(
                tools=tools,  # Python functions passed directly
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode='AUTO'
                    )                ),
                system_instruction=system_instructions,
                temperature=0.0
            )

            # Send request with full context
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=all_contents,
                config=config
            )
        else:
            # Simple text generation with system instructions
            config = types.GenerateContentConfig(
                system_instruction=system_instructions
            )

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=all_contents,
                config=config
            )

        return response.text if response.text else ""
    
    def generate_text(self, prompt: str) -> str:
        """Simple text generation using new SDK"""
        client = self._create_client()
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        return response.text


# Global client instance
_gemini_client = None


def get_gemini_client() -> GeminiClient:
    """Get the global Gemini client"""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
