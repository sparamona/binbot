"""
Test to check actual embedding dimensions from Gemini
"""

import sys
import os
sys.path.append('.')

# Set memory mode
os.environ['STORAGE_MODE'] = 'memory'

from llm.embeddings import get_embedding_service
from config.embeddings import EMBEDDING_DIMENSION, EMBEDDING_MODEL

def test_embedding_dimensions():
    print("🧪 Testing embedding dimensions...")
    
    try:
        service = get_embedding_service()
        
        # Test single embedding
        embedding = service.generate_embedding("test text")
        actual_dimension = len(embedding)
        
        print(f"📊 Embedding Model: {EMBEDDING_MODEL}")
        print(f"📊 Expected Dimension: {EMBEDDING_DIMENSION}")
        print(f"📊 Actual Dimension: {actual_dimension}")
        
        if actual_dimension == EMBEDDING_DIMENSION:
            print("✅ Embedding dimensions match!")
        else:
            print(f"⚠️ Dimension mismatch! Expected {EMBEDDING_DIMENSION}, got {actual_dimension}")
            print("💡 Consider updating EMBEDDING_DIMENSION in config/embeddings.py")
        
        # Test batch embeddings
        batch_embeddings = service.batch_generate_embeddings(["text 1", "text 2"])
        print(f"📊 Batch embeddings: {len(batch_embeddings)} items, each with {len(batch_embeddings[0])} dimensions")
        
        return actual_dimension
        
    except Exception as e:
        print(f"❌ Error testing embeddings: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_embedding_dimensions()
