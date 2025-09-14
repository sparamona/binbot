import hashlib
from typing import List, Optional
from .client import LLMClient


class EmbeddingService:
    """Embedding generation service for BinBot"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using available LLM service"""
        if not text.strip():
            return None

        try:
            if self.llm_client.provider == "openai" and self.llm_client.openai_client:
                response = self.llm_client.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=text
                )
                return response.data[0].embedding
            elif self.llm_client.provider == "gemini" and self.llm_client.gemini_model:
                # Note: Gemini doesn't have a direct embedding API yet
                # For now, fall back to hash-based embeddings
                return self.generate_hash_embedding(text)
            else:
                # Fall back to hash-based embeddings
                return self.generate_hash_embedding(text)
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return self.generate_hash_embedding(text)

    def generate_hash_embedding(self, text: str) -> List[float]:
        """Generate hash-based embedding as fallback"""
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert to 384-dimensional embedding
        embedding = []
        for i in range(384):
            byte_index = i % len(hash_bytes)
            embedding.append((hash_bytes[byte_index] / 255.0) * 2.0 - 1.0)

        return embedding
