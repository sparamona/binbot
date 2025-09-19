#!/usr/bin/env python3
"""
Test script to verify the refactored LLM integration works correctly
"""

import os
import sys
import asyncio
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print(f"⚠️  No .env file found at {env_path}")

# Load environment variables
load_env_file()

def test_imports():
    """Test that all imports work correctly"""
    print("🔄 Testing imports...")
    
    try:
        from llm.client import LLMClient, OpenAIProvider, GeminiProvider, BaseLLMProvider
        from llm.embeddings import EmbeddingService
        from llm.vision import VisionService
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_llm_client_initialization():
    """Test LLM client initialization"""
    print("\n🔄 Testing LLM client initialization...")
    
    try:
        # Mock config
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
        
        from llm.client import LLMClient
        client = LLMClient(config)
        
        # Test initialization
        success = client.initialize()
        
        if success:
            print(f"✅ LLM client initialized successfully with provider: {client.provider_name}")
            print(f"   Provider type: {type(client.provider).__name__}")
            return True
        else:
            print("❌ LLM client initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ LLM client initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_embedding_service():
    """Test embedding service"""
    print("\n🔄 Testing embedding service...")
    
    try:
        config = {
            "llm": {
                "provider": "openai",
                "openai": {
                    "model": "gpt-4",
                    "embedding_model": "text-embedding-ada-002"
                }
            }
        }
        
        from llm.client import LLMClient
        from llm.embeddings import EmbeddingService
        
        client = LLMClient(config)
        if not client.initialize():
            print("❌ Could not initialize LLM client for embedding test")
            return False
            
        embedding_service = EmbeddingService(client)
        
        # Test embedding generation
        test_text = "This is a test item for embedding"
        embedding = embedding_service.generate_embedding(test_text)
        
        if embedding and len(embedding) > 0:
            print(f"✅ Embedding generated successfully: {len(embedding)} dimensions")
            return True
        else:
            print("❌ Embedding generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Embedding service error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vision_service():
    """Test vision service initialization"""
    print("\n🔄 Testing vision service...")
    
    try:
        config = {
            "llm": {
                "provider": "openai",
                "openai": {
                    "model": "gpt-4",
                    "embedding_model": "text-embedding-ada-002"
                }
            }
        }
        
        from llm.client import LLMClient
        from llm.vision import VisionService
        
        client = LLMClient(config)
        if not client.initialize():
            print("❌ Could not initialize LLM client for vision test")
            return False
            
        vision_service = VisionService(config, client)
        
        # Test initialization
        success = vision_service.initialize()
        
        if success:
            print("✅ Vision service initialized successfully")
            return True
        else:
            print("❌ Vision service initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Vision service error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_chat_completion():
    """Test chat completion"""
    print("\n🔄 Testing chat completion...")
    
    try:
        config = {
            "llm": {
                "provider": "openai",
                "openai": {
                    "model": "gpt-4",
                    "embedding_model": "text-embedding-ada-002"
                }
            }
        }
        
        from llm.client import LLMClient
        
        client = LLMClient(config)
        if not client.initialize():
            print("❌ Could not initialize LLM client for chat test")
            return False
            
        # Test simple chat completion
        messages = [
            {"role": "user", "content": "Say 'Hello, refactored LLM!' if you can understand this message."}
        ]
        
        response = await client.chat_completion(
            messages=messages,
            temperature=0.1,
            max_tokens=50
        )
        
        if response and response.content:
            print(f"✅ Chat completion successful: {response.content[:100]}...")
            return True
        else:
            print("❌ Chat completion failed")
            return False
            
    except Exception as e:
        print(f"❌ Chat completion error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Testing Refactored LLM Integration")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("LLM Client Initialization", test_llm_client_initialization),
        ("Embedding Service", test_embedding_service),
        ("Vision Service", test_vision_service),
        ("Chat Completion", test_chat_completion),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
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
        print("🎉 All tests passed! Refactored LLM integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())
