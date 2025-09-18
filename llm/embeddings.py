from typing import List, Optional
from .client import LLMClient


class EmbeddingService:
    """Embedding generation service for BinBot"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using OpenAI embedding service"""
        if not text.strip():
            return None

        try:
            if self.llm_client.provider == "openai" and self.llm_client.openai_client:
                response = self.llm_client.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=text
                )
                # Extract the embedding directly to avoid Pydantic validation issues
                embedding = response.data[0].embedding
                # Ensure we return a plain list of floats
                return list(embedding) if embedding else None
            else:
                raise ValueError(f"Embedding service requires OpenAI provider, but current provider is: {self.llm_client.provider}")
        except Exception as e:
            print(f"Error generating embedding: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Full traceback:")
            traceback.print_exc()
            raise e
