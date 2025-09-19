#!/usr/bin/env python3
"""
Basic test to verify the refactored LLM structure is correct
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_class_structure():
    """Test that the class structure is correct"""
    print("🔄 Testing class structure...")
    
    try:
        from llm.client import (
            BaseLLMProvider, 
            OpenAIProvider, 
            GeminiProvider, 
            LLMClient,
            ChatResponse,
            VisionResponse
        )
        
        # Test that classes exist and have expected methods
        assert hasattr(BaseLLMProvider, 'initialize')
        assert hasattr(BaseLLMProvider, 'chat_completion')
        assert hasattr(BaseLLMProvider, 'generate_embedding')
        assert hasattr(BaseLLMProvider, 'analyze_image')
        
        assert hasattr(OpenAIProvider, 'initialize')
        assert hasattr(GeminiProvider, 'initialize')
        assert hasattr(LLMClient, 'initialize')
        
        print("✅ All classes and methods exist")
        return True
        
    except Exception as e:
        print(f"❌ Class structure test failed: {e}")
        return False

def test_provider_instantiation():
    """Test that providers can be instantiated"""
    print("\n🔄 Testing provider instantiation...")
    
    try:
        from llm.client import OpenAIProvider, GeminiProvider, LLMClient
        
        config = {
            "llm": {
                "provider": "openai",
                "openai": {
                    "model": "gpt-4",
                    "embedding_model": "text-embedding-ada-002"
                },
                "gemini": {
                    "model": "gemini-pro"
                }
            }
        }
        
        # Test OpenAI provider instantiation
        openai_provider = OpenAIProvider(config)
        assert openai_provider.provider_name == "openai"
        assert openai_provider.chat_model == "gpt-4"
        
        # Test Gemini provider instantiation
        gemini_provider = GeminiProvider(config)
        assert gemini_provider.provider_name == "gemini"
        assert gemini_provider.chat_model_name == "gemini-pro"
        
        # Test LLM client instantiation
        llm_client = LLMClient(config)
        assert llm_client.config == config
        
        print("✅ All providers can be instantiated correctly")
        return True
        
    except Exception as e:
        print(f"❌ Provider instantiation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_embedding_service_structure():
    """Test embedding service structure"""
    print("\n🔄 Testing embedding service structure...")
    
    try:
        from llm.embeddings import EmbeddingService
        from llm.client import LLMClient
        
        config = {"llm": {"provider": "openai"}}
        client = LLMClient(config)
        
        embedding_service = EmbeddingService(client)
        assert hasattr(embedding_service, 'generate_embedding')
        assert embedding_service.llm_client == client
        
        print("✅ Embedding service structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Embedding service test failed: {e}")
        return False

def test_vision_service_structure():
    """Test vision service structure"""
    print("\n🔄 Testing vision service structure...")
    
    try:
        from llm.vision import VisionService
        from llm.client import LLMClient
        
        config = {"llm": {"provider": "openai"}}
        client = LLMClient(config)
        
        vision_service = VisionService(config, client)
        assert hasattr(vision_service, 'identify_item')
        assert hasattr(vision_service, 'search_by_image')
        assert hasattr(vision_service, 'describe_for_accessibility')
        assert vision_service.llm_client == client
        
        print("✅ Vision service structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Vision service test failed: {e}")
        return False

def test_response_classes():
    """Test response classes"""
    print("\n🔄 Testing response classes...")
    
    try:
        from llm.client import ChatResponse, VisionResponse
        
        # Test ChatResponse
        chat_response = ChatResponse(content="test", tool_calls=None, usage=None)
        assert chat_response.content == "test"
        
        # Test VisionResponse
        vision_response = VisionResponse(success=True, content="test", error=None)
        assert vision_response.success == True
        assert vision_response.content == "test"
        
        print("✅ Response classes work correctly")
        return True
        
    except Exception as e:
        print(f"❌ Response classes test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Refactored LLM Structure")
    print("=" * 50)
    
    tests = [
        ("Class Structure", test_class_structure),
        ("Provider Instantiation", test_provider_instantiation),
        ("Embedding Service Structure", test_embedding_service_structure),
        ("Vision Service Structure", test_vision_service_structure),
        ("Response Classes", test_response_classes),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All structural tests passed! Refactored LLM integration structure is correct.")
        print("\n💡 Next steps:")
        print("   - Start the Docker container to test with actual API calls")
        print("   - Run: docker-compose --env-file .env up --build")
        print("   - Test endpoints: curl http://localhost:8000/health")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    main()
