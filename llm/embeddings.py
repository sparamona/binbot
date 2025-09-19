from typing import List, Optional
from .client import LLMClient


class EmbeddingService:
    """Embedding generation service for BinBot"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using the active LLM provider"""
        if not text.strip():
            return None

        try:
            return self.llm_client.generate_embedding(text)
        except Exception as e:
            print(f"Error generating embedding: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Full traceback:")
            traceback.print_exc()
            raise e
