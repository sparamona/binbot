"""
Integration test for API endpoints
Tests that all major API components work together
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set memory mode for clean testing
os.environ['STORAGE_MODE'] = 'memory'

import asyncio
from api.health import health_check
from api.session import start_session, get_session
from api.chat import create_function_mapping
from chat.function_wrappers import get_function_wrappers
from session.session_manager import get_session_manager


class MockResponse:
    def __init__(self):
        self.cookies = {}
        
    def set_cookie(self, key, value, **kwargs):
        self.cookies[key] = value


async def test_api_integration():
    """Test that all API components work together"""
    print("API Integration Test")
    print("=" * 30)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    health_response = await health_check()
    assert health_response.status == "ok"
    print("   Health check: OK")
    
    # Test 2: Session creation
    print("\n2. Testing session creation...")
    mock_response = MockResponse()
    session_response = await start_session(mock_response)
    assert session_response.success is True
    session_id = session_response.session_id
    assert "session_id" in mock_response.cookies
    print(f"   Session created: {session_id[:8]}...")
    
    # Test 3: Session retrieval
    print("\n3. Testing session retrieval...")
    session_info_response = await get_session(session_id)
    assert session_info_response.success is True
    assert session_info_response.session.session_id == session_id
    print("   Session retrieved successfully")
    
    # Test 4: Function wrappers
    print("\n4. Testing function wrappers...")
    wrappers = get_function_wrappers(session_id)
    function_mapping = create_function_mapping(wrappers)
    assert len(function_mapping) == 5
    expected_functions = ["add_items", "search_items", "get_bin_contents", "move_items", "remove_items"]
    for func_name in expected_functions:
        assert func_name in function_mapping
        assert callable(function_mapping[func_name])
    print("   Function mapping: OK")
    
    # Test 5: Session conversation
    print("\n5. Testing session conversation...")
    session_manager = get_session_manager()
    session_manager.add_message(session_id, "user", "Hello")
    session_manager.add_message(session_id, "assistant", "Hi there!")
    
    conversation = session_manager.get_conversation(session_id)
    assert len(conversation) == 2
    assert conversation[0]["role"] == "user"
    assert conversation[1]["role"] == "assistant"
    print("   Conversation management: OK")
    
    print("\nAll API integration tests passed!")
    return True


if __name__ == "__main__":
    print("BinBot API Integration Test")
    print("Tests core API functionality without external dependencies")
    print()
    
    success = asyncio.run(test_api_integration())
    
    print("\n" + "=" * 50)
    if success:
        print("SUCCESS: API integration test passed!")
    else:
        print("FAILED: API integration test failed!")
