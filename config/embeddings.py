"""
Centralized embedding configuration for BinBot
"""

# OpenAI text-embedding-ada-002 produces 1536-dimensional embeddings
OPENAI_EMBEDDING_DIMENSION = 1536

# Default embedding dimension for the system (OpenAI only)
DEFAULT_EMBEDDING_DIMENSION = OPENAI_EMBEDDING_DIMENSION

# Embedding model configurations
EMBEDDING_MODELS = {
    "openai": {
        "model": "text-embedding-ada-002",
        "dimension": OPENAI_EMBEDDING_DIMENSION,
        "provider": "openai"
    }
}

def get_embedding_dimension(model_name: str = "openai") -> int:
    """Get embedding dimension for a specific model"""
    return EMBEDDING_MODELS.get(model_name, {}).get("dimension", DEFAULT_EMBEDDING_DIMENSION)

def get_model_info(embedding_length: int) -> dict:
    """Get model info based on embedding length"""
    for model_name, config in EMBEDDING_MODELS.items():
        if config["dimension"] == embedding_length:
            return {"name": model_name, **config}

    # Default fallback
    return {"name": "unknown", "model": "unknown", "dimension": embedding_length, "provider": "unknown"}
