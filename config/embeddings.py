"""
Embeddings Configuration for BinBot - Simple constants
"""

import os

# Simple embedding configuration
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-004')
EMBEDDING_BATCH_SIZE = int(os.getenv('EMBEDDING_BATCH_SIZE', '100'))

# Embedding dimensions for different models
# text-embedding-004: 768 dimensions
# text-embedding-3-small: 1536 dimensions
# text-embedding-3-large: 3072 dimensions
EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', '768'))
