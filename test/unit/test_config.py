"""
Tests for simplified BinBot configuration system
"""

import os
import sys
sys.path.append('.')

from config.settings import GEMINI_API_KEY, DATABASE_PATH, API_PORT, SESSION_TTL_MINUTES
from config.embeddings import EMBEDDING_MODEL, EMBEDDING_BATCH_SIZE


def test_config_constants():
    """Test that configuration constants are accessible"""
    print("🧪 Testing simplified configuration...")

    # Test that constants exist and have reasonable values
    assert GEMINI_API_KEY is not None, "GEMINI_API_KEY should be set"
    assert DATABASE_PATH == './data/chromadb', f"Expected './data/chromadb', got {DATABASE_PATH}"
    assert API_PORT == 8000, f"Expected 8000, got {API_PORT}"
    assert SESSION_TTL_MINUTES == 30, f"Expected 30, got {SESSION_TTL_MINUTES}"

    print(f"✅ API Key present: {bool(GEMINI_API_KEY)}")
    print(f"✅ Database path: {DATABASE_PATH}")
    print(f"✅ API port: {API_PORT}")
    print(f"✅ Session TTL: {SESSION_TTL_MINUTES} minutes")

    # Test embedding config
    assert EMBEDDING_MODEL == 'text-embedding-004'
    assert EMBEDDING_BATCH_SIZE == 100

    print(f"✅ Embedding model: {EMBEDDING_MODEL}")
    print(f"✅ Embedding batch size: {EMBEDDING_BATCH_SIZE}")

    return True


if __name__ == "__main__":
    print("🧪 Testing simplified configuration system...")
    print("=" * 50)

    try:
        success = test_config_constants()
        print("\n" + "=" * 50)
        if success:
            print("🎉 All configuration tests passed!")
        else:
            print("❌ Configuration tests failed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
