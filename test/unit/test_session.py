"""
Tests for session management
"""

import sys
import time
sys.path.append('.')

from session.session_manager import SessionManager


def test_session_basic_operations():
    """Test basic session operations"""
    print("🧪 Testing session basic operations...")
    
    manager = SessionManager()
    
    # Create session
    session_id = manager.new_session()
    assert session_id is not None
    assert len(session_id) > 0
    print(f"✅ Created session: {session_id[:8]}...")
    
    # Get session
    session = manager.get_session(session_id)
    assert session is not None
    assert session['session_id'] == session_id
    assert session['current_bin'] == ''
    assert session['conversation'] == []
    print("✅ Retrieved session successfully")
    
    # Set current bin
    manager.set_current_bin(session_id, 'A3')
    session = manager.get_session(session_id)
    assert session['current_bin'] == 'A3'
    print("✅ Set current bin")
    
    # Add messages
    manager.add_message(session_id, 'user', 'Hello')
    manager.add_message(session_id, 'assistant', 'Hi there!')
    
    conversation = manager.get_conversation(session_id)
    assert len(conversation) == 2
    assert conversation[0]['role'] == 'user'
    assert conversation[0]['content'] == 'Hello'
    assert conversation[1]['role'] == 'assistant'
    print("✅ Added messages to conversation")
    
    # End session
    manager.end_session(session_id)
    session = manager.get_session(session_id)
    assert session is None
    print("✅ Ended session")
    
    return True


def test_session_expiration():
    """Test session expiration (simplified)"""
    print("🧪 Testing session expiration...")
    
    manager = SessionManager()
    
    # Create session
    session_id = manager.new_session()
    session = manager.get_session(session_id)
    assert session is not None
    print("✅ Created session")
    
    # Manually expire session by modifying last_accessed
    from datetime import datetime, timedelta
    session['last_accessed'] = datetime.now() - timedelta(hours=1)
    
    # Try to get expired session
    expired_session = manager.get_session(session_id)
    assert expired_session is None
    print("✅ Expired session was removed")
    
    return True


def test_cleanup():
    """Test cleanup of expired sessions"""
    print("🧪 Testing session cleanup...")
    
    manager = SessionManager()
    
    # Create multiple sessions
    session_ids = []
    for i in range(3):
        session_id = manager.new_session()
        session_ids.append(session_id)
    
    print(f"✅ Created {len(session_ids)} sessions")
    
    # Manually expire some sessions
    from datetime import datetime, timedelta
    for i in range(2):  # Expire first 2 sessions
        session = manager._sessions[session_ids[i]]
        session['last_accessed'] = datetime.now() - timedelta(hours=1)
    
    # Run cleanup
    cleaned_count = manager.cleanup_expired_sessions()
    assert cleaned_count == 2
    print(f"✅ Cleaned up {cleaned_count} expired sessions")
    
    # Verify remaining session still exists
    remaining_session = manager.get_session(session_ids[2])
    assert remaining_session is not None
    print("✅ Non-expired session still exists")
    
    return True


if __name__ == "__main__":
    print("🧪 Testing session management...")
    print("=" * 50)
    
    try:
        test_session_basic_operations()
        print()
        test_session_expiration()
        print()
        test_cleanup()
        
        print("\n" + "=" * 50)
        print("🎉 All session management tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
