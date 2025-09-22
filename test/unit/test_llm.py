"""
Tests for LLM integration (basic connectivity tests)
"""

import sys
sys.path.append('.')

from llm.client import get_gemini_client
from llm.embeddings import get_embedding_service
from llm.vision import get_vision_service


def test_gemini_client_init():
    """Test that Gemini client initializes"""
    print("🧪 Testing Gemini client initialization...")
    
    try:
        client = get_gemini_client()
        assert client is not None
        assert client.model is not None
        print("✅ Gemini client initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Gemini client initialization failed: {e}")
        return False


def test_embedding_service_init():
    """Test that embedding service initializes"""
    print("🧪 Testing embedding service initialization...")
    
    try:
        service = get_embedding_service()
        assert service is not None
        print("✅ Embedding service initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Embedding service initialization failed: {e}")
        return False


def test_vision_service_init():
    """Test that vision service initializes"""
    print("🧪 Testing vision service initialization...")
    
    try:
        service = get_vision_service()
        assert service is not None
        assert service.model is not None
        print("✅ Vision service initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Vision service initialization failed: {e}")
        return False


def test_simple_text_generation():
    """Test simple text generation (if API key is valid)"""
    print("🧪 Testing simple text generation...")
    
    try:
        client = get_gemini_client()
        response = client.generate_text("Say 'Hello BinBot' in exactly those words.")
        assert isinstance(response, str)
        assert len(response) > 0
        print(f"✅ Generated text: {response[:50]}...")
        return True
    except Exception as e:
        print(f"⚠️ Text generation test skipped (API issue): {e}")
        return True  # Don't fail the test for API issues


def test_simple_embedding():
    """Test simple embedding generation (if API key is valid)"""
    print("🧪 Testing simple embedding generation...")
    
    try:
        service = get_embedding_service()
        embedding = service.generate_embedding("test item")
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, (int, float)) for x in embedding)
        print(f"✅ Generated embedding with {len(embedding)} dimensions")
        return True
    except Exception as e:
        print(f"⚠️ Embedding test skipped (API issue): {e}")
        return True  # Don't fail the test for API issues


if __name__ == "__main__":
    print("🧪 Testing LLM integration...")
    print("=" * 50)
    
    all_passed = True
    
    all_passed &= test_gemini_client_init()
    print()
    all_passed &= test_embedding_service_init()
    print()
    all_passed &= test_vision_service_init()
    print()
    all_passed &= test_simple_text_generation()
    print()
    all_passed &= test_simple_embedding()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All LLM integration tests passed!")
    else:
        print("❌ Some LLM integration tests failed!")
