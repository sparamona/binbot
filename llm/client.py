import os
from typing import Dict, Any, Optional

# LLM Integration imports
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False


class LLMClient:
    """LLM client for BinBot AI functionality"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.openai_client: Optional[Any] = None
        self.gemini_model: Optional[Any] = None
        self.provider: Optional[str] = None
    
    def initialize(self):
        """Initialize LLM clients based on available API keys and configuration"""
        openai_key = os.environ.get('OPENAI_API_KEY')
        gemini_key = os.environ.get('GEMINI_API_KEY')

        # Try to initialize OpenAI client
        if openai_key and openai_key != "${OPENAI_API_KEY}" and OPENAI_AVAILABLE:
            try:
                print(f"DEBUG: Attempting to initialize OpenAI client...")
                print(f"DEBUG: OpenAI available: {OPENAI_AVAILABLE}")
                print(f"DEBUG: API key present: {bool(openai_key)}")
                print(f"DEBUG: API key starts with: {openai_key[:10]}..." if openai_key else "No key")
                print(f"DEBUG: OpenAI version: {openai.__version__}")
                
                # Initialize OpenAI client with minimal configuration
                self.openai_client = openai.OpenAI(api_key=openai_key)
                self.provider = "openai"
                print("OpenAI client initialized successfully")
            except Exception as e:
                print(f"Failed to initialize OpenAI client: {e}")
                print(f"DEBUG: Exception type: {type(e)}")
                print(f"DEBUG: Exception args: {e.args}")
                import traceback
                print(f"DEBUG: Full traceback:")
                traceback.print_exc()
                self.openai_client = None

        # Try to initialize Gemini client
        if gemini_key and gemini_key != "${GEMINI_API_KEY}" and GOOGLE_AI_AVAILABLE and self.provider is None:
            try:
                genai.configure(api_key=gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                self.provider = "gemini"
                print("Gemini client initialized successfully")
            except Exception as e:
                print(f"Failed to initialize Gemini client: {e}")
                self.gemini_model = None

        if self.provider is None:
            print("No LLM clients initialized. Set OPENAI_API_KEY or GEMINI_API_KEY environment variable.")
    
    def validate_connection(self) -> bool:
        """Validate external LLM API connectivity"""
        try:
            # Check if any LLM client is initialized
            return self.provider is not None and (self.openai_client is not None or self.gemini_model is not None)
        except Exception as e:
            print(f"LLM connection validation error: {e}")
            return False
