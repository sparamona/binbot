import os
import base64
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

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


@dataclass
class ChatMessage:
    """Standardized chat message format"""
    role: str  # "user", "assistant", "system"
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class ChatResponse:
    """Standardized chat response format"""
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    usage: Optional[Dict[str, Any]] = None


@dataclass
class VisionResponse:
    """Standardized vision analysis response"""
    success: bool
    content: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = "base"

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the provider with API keys and configuration"""
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate the connection to the provider"""
        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """Generate chat completion"""
        pass

    @abstractmethod
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate text embedding"""
        pass

    @abstractmethod
    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        max_tokens: int = 300,
        temperature: float = 0.1,
        response_format: Optional[str] = None
    ) -> VisionResponse:
        """Analyze image with vision capabilities"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_name = "openai"
        self.client: Optional[Any] = None
        self.chat_model = config.get("llm", {}).get("openai", {}).get("model", "gpt-4")
        self.vision_model = "gpt-4o"  # Best model for vision
        self.embedding_model = config.get("llm", {}).get("openai", {}).get("embedding_model", "text-embedding-ada-002")

    def initialize(self) -> bool:
        """Initialize OpenAI client"""
        if not OPENAI_AVAILABLE:
            print("OpenAI library not available")
            return False

        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key or api_key == "${OPENAI_API_KEY}":
            print("OpenAI API key not found")
            return False

        try:
            self.client = openai.OpenAI(api_key=api_key)
            print("OpenAI provider initialized successfully")
            return True
        except Exception as e:
            print(f"Failed to initialize OpenAI provider: {e}")
            return False

    def validate_connection(self) -> bool:
        """Validate OpenAI connection"""
        return self.client is not None

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """Generate chat completion using OpenAI"""
        if not self.client:
            raise Exception("OpenAI client not initialized")

        try:
            request_params = {
                "model": self.chat_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            if tools:
                request_params["tools"] = tools
                if tool_choice:
                    request_params["tool_choice"] = tool_choice

            response = self.client.chat.completions.create(**request_params)

            choice = response.choices[0]
            message = choice.message

            return ChatResponse(
                content=message.content or "",
                tool_calls=getattr(message, 'tool_calls', None),
                usage=response.usage.model_dump() if hasattr(response, 'usage') else None
            )

        except Exception as e:
            print(f"OpenAI chat completion error: {e}")
            raise

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using OpenAI"""
        if not self.client or not text.strip():
            return None

        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            embedding = response.data[0].embedding
            return list(embedding) if embedding else None
        except Exception as e:
            print(f"OpenAI embedding error: {e}")
            raise

    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        max_tokens: int = 300,
        temperature: float = 0.1,
        response_format: Optional[str] = None
    ) -> VisionResponse:
        """Analyze image using OpenAI Vision"""
        if not self.client:
            return VisionResponse(success=False, error="OpenAI client not initialized")

        try:
            # Encode image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')

            # Prepare request
            request_params = {
                "model": self.vision_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            if response_format == "json_object":
                request_params["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**request_params)
            content = response.choices[0].message.content

            # Try to parse as JSON if requested
            structured_data = None
            if response_format == "json_object" and content:
                try:
                    structured_data = json.loads(content)
                except json.JSONDecodeError:
                    pass

            return VisionResponse(
                success=True,
                content=content,
                structured_data=structured_data
            )

        except Exception as e:
            return VisionResponse(
                success=False,
                error=f"OpenAI vision error: {str(e)}"
            )


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider implementation"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_name = "gemini"
        self.model = None
        self.vision_model = None
        self.chat_model_name = config.get("llm", {}).get("gemini", {}).get("model", "gemini-pro")
        self.vision_model_name = "gemini-pro-vision"

    def initialize(self) -> bool:
        """Initialize Gemini client"""
        if not GOOGLE_AI_AVAILABLE:
            print("Google AI library not available")
            return False

        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key or api_key == "${GEMINI_API_KEY}":
            print("Gemini API key not found")
            return False

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.chat_model_name)
            self.vision_model = genai.GenerativeModel(self.vision_model_name)
            print("Gemini provider initialized successfully")
            return True
        except Exception as e:
            print(f"Failed to initialize Gemini provider: {e}")
            return False

    def validate_connection(self) -> bool:
        """Validate Gemini connection"""
        return self.model is not None

    def _convert_messages_to_gemini_prompt(self, messages: List[Dict[str, Any]]) -> str:
        """Convert OpenAI-style messages to Gemini prompt format"""
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        return "\n\n".join(prompt_parts)

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """Generate chat completion using Gemini"""
        if not self.model:
            raise Exception("Gemini model not initialized")

        try:
            # Convert messages to Gemini format
            prompt = self._convert_messages_to_gemini_prompt(messages)

            # Note: Gemini doesn't support function calling in the same way as OpenAI
            # This is a simplified implementation
            if tools:
                print("Warning: Function calling not fully supported with Gemini provider")

            response = self.model.generate_content(prompt)

            return ChatResponse(
                content=response.text,
                tool_calls=None,  # Gemini doesn't support tool calls in the same format
                usage=None
            )

        except Exception as e:
            print(f"Gemini chat completion error: {e}")
            raise

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using Gemini"""
        # Note: Gemini doesn't have a direct embedding API like OpenAI
        # This would need to be implemented using a different approach
        # For now, we'll raise an exception to indicate it's not supported
        raise NotImplementedError("Gemini embedding generation not yet implemented")

    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        max_tokens: int = 300,
        temperature: float = 0.1,
        response_format: Optional[str] = None
    ) -> VisionResponse:
        """Analyze image using Gemini Vision"""
        if not self.vision_model:
            return VisionResponse(success=False, error="Gemini vision model not initialized")

        try:
            # Gemini expects PIL Image objects
            from PIL import Image
            import io

            image = Image.open(io.BytesIO(image_data))

            response = self.vision_model.generate_content([prompt, image])
            content = response.text

            # Try to parse as JSON if requested
            structured_data = None
            if response_format == "json_object" and content:
                try:
                    structured_data = json.loads(content)
                except json.JSONDecodeError:
                    pass

            return VisionResponse(
                success=True,
                content=content,
                structured_data=structured_data
            )

        except Exception as e:
            return VisionResponse(
                success=False,
                error=f"Gemini vision error: {str(e)}"
            )


class LLMClient:
    """Unified LLM client that delegates to provider-specific implementations"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider: Optional[BaseLLMProvider] = None
        self.provider_name: Optional[str] = None

    def initialize(self) -> bool:
        """Initialize LLM provider based on available API keys and configuration"""
        # Check configuration preference first
        preferred_provider = self.config.get("llm", {}).get("provider", "openai")

        # Try to initialize preferred provider first
        if preferred_provider == "openai":
            if self._try_initialize_openai():
                return True
            elif self._try_initialize_gemini():
                return True
        else:  # preferred_provider == "gemini"
            if self._try_initialize_gemini():
                return True
            elif self._try_initialize_openai():
                return True

        print("No LLM providers could be initialized. Check your API keys.")
        return False

    def _try_initialize_openai(self) -> bool:
        """Try to initialize OpenAI provider"""
        try:
            provider = OpenAIProvider(self.config)
            if provider.initialize():
                self.provider = provider
                self.provider_name = "openai"
                return True
        except Exception as e:
            print(f"Failed to initialize OpenAI provider: {e}")
        return False

    def _try_initialize_gemini(self) -> bool:
        """Try to initialize Gemini provider"""
        try:
            provider = GeminiProvider(self.config)
            if provider.initialize():
                self.provider = provider
                self.provider_name = "gemini"
                return True
        except Exception as e:
            print(f"Failed to initialize Gemini provider: {e}")
        return False
    
    def validate_connection(self) -> bool:
        """Validate external LLM API connectivity"""
        if not self.provider:
            return False
        return self.provider.validate_connection()

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None
    ) -> ChatResponse:
        """Generate chat completion using the active provider"""
        if not self.provider:
            raise Exception("No LLM provider initialized")

        return await self.provider.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            tool_choice=tool_choice
        )

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate text embedding using the active provider"""
        if not self.provider:
            return None
        return self.provider.generate_embedding(text)

    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        max_tokens: int = 300,
        temperature: float = 0.1,
        response_format: Optional[str] = None
    ) -> VisionResponse:
        """Analyze image using the active provider"""
        if not self.provider:
            return VisionResponse(success=False, error="No LLM provider initialized")

        return await self.provider.analyze_image(
            image_data=image_data,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format=response_format
        )
