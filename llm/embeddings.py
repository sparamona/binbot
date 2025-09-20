"""
Simple embeddings service using Gemini
"""

import google.generativeai as genai
from typing import List

from config.settings import GEMINI_API_KEY
from config.embeddings import EMBEDDING_MODEL


class EmbeddingService:
    """Simple embedding service using Gemini"""
    
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        result = genai.embed_content(
            model=f"models/{EMBEDDING_MODEL}",
            content=text
        )
        return result['embedding']
    
    def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings


# Global embedding service instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get the global embedding service"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
