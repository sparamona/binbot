"""
Simple Gemini LLM client for BinBot
"""

import google.generativeai as genai
from typing import List, Dict, Any

from config.settings import GEMINI_API_KEY


class GeminiClient:
    """Simple Gemini LLM client"""
    
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def chat_completion(self, messages: List[Dict[str, str]], tools: List = None) -> str:
        """Send messages to Gemini and get response"""
        # Convert messages to Gemini format
        chat_history = []
        for msg in messages[:-1]:  # All but the last message
            chat_history.append({
                'role': 'user' if msg['role'] == 'user' else 'model',
                'parts': [msg['content']]
            })
        
        # Start chat with history
        chat = self.model.start_chat(history=chat_history)
        
        # Send the latest message
        latest_message = messages[-1]['content']
        
        if tools:
            # Configure tools for function calling
            tool_config = genai.protos.ToolConfig(
                function_calling_config=genai.protos.FunctionCallingConfig(
                    mode=genai.protos.FunctionCallingConfig.Mode.AUTO
                )
            )
            
            response = chat.send_message(
                latest_message,
                tools=tools,
                tool_config=tool_config
            )
        else:
            response = chat.send_message(latest_message)
        
        return response.text
    
    def generate_text(self, prompt: str) -> str:
        """Simple text generation"""
        response = self.model.generate_content(prompt)
        return response.text


# Global client instance
_gemini_client = None


def get_gemini_client() -> GeminiClient:
    """Get the global Gemini client"""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
