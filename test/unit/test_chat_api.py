"""
Tests for chat API endpoints
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set memory mode for clean testing
os.environ['STORAGE_MODE'] = 'memory'

import asyncio
from api.chat import create_function_mapping
from api_schemas import ChatRequest
from chat.function_wrappers import get_function_wrappers
from session.session_manager import get_session_manager


async def test_function_mapping():
    """Test function mapping creation"""
    print("🧪 Testing Function Mapping")
    print("=" * 30)
    
    # Create a test session
    session_manager = get_session_manager()
    session_id = session_manager.new_session()
    print(f"📝 Created test session: {session_id[:8]}...")
    
    # Create function wrappers
    wrappers = get_function_wrappers(session_id)
    function_mapping = create_function_mapping(wrappers)
    
    print(f"📋 Function mapping created with {len(function_mapping)} functions")
    
    # Check that all expected functions are mapped
    expected_functions = ["add_items", "search_items", "get_bin_contents", "move_items", "remove_items"]
    
    for func_name in expected_functions:
        assert func_name in function_mapping
        assert callable(function_mapping[func_name])
        print(f"✅ {func_name} mapped correctly")
    
    print("✅ Function mapping working correctly")
    return True


async def test_chat_request_validation():
    """Test chat request validation"""
    print("\n🧪 Testing Chat Request Validation")
    print("=" * 35)
    
    # Test valid request
    valid_request = ChatRequest(
        message="Hello BinBot",
        session_id="test-session-123"
    )
    
    assert valid_request.message == "Hello BinBot"
    assert valid_request.session_id == "test-session-123"
    print("✅ Valid chat request created")
    
    # Test request validation
    try:
        invalid_request = ChatRequest(
            message="",  # Empty message
            session_id="test-session-123"
        )
        # This should work as empty string is valid
        print("✅ Empty message handled")
    except Exception as e:
        print(f"📋 Validation error (expected): {e}")
    
    return True


async def test_session_conversation():
    """Test session conversation management"""
    print("\n🧪 Testing Session Conversation")
    print("=" * 32)
    
    # Create a test session
    session_manager = get_session_manager()
    session_id = session_manager.new_session()
    print(f"📝 Created test session: {session_id[:8]}...")
    
    # Add messages to conversation
    session_manager.add_message(session_id, "user", "Hello")
    session_manager.add_message(session_id, "assistant", "Hi there!")
    session_manager.add_message(session_id, "user", "What's in bin A3?")
    
    # Get conversation
    conversation = session_manager.get_conversation(session_id)
    
    print(f"📋 Conversation has {len(conversation)} messages")
    assert len(conversation) == 3
    assert conversation[0]["role"] == "user"
    assert conversation[0]["content"] == "Hello"
    assert conversation[1]["role"] == "assistant"
    assert conversation[2]["role"] == "user"
    
    print("✅ Session conversation working correctly")
    return True


if __name__ == "__main__":
    print("💬 BinBot Chat API Test")
    print("Tests chat functionality and session management")
    print()
    
    async def run_all_tests():
        success1 = await test_function_mapping()
        success2 = await test_chat_request_validation()
        success3 = await test_session_conversation()
        return success1 and success2 and success3
    
    success = asyncio.run(run_all_tests())
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Chat API tests passed!")
    else:
        print("❌ Chat API tests failed!")
