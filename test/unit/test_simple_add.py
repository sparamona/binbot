"""
Simple test for add_items functionality
"""

import sys
sys.path.append('.')

from chat.function_wrappers import get_function_wrappers
from session.session_manager import get_session_manager

def test_simple_add():
    print("🧪 Testing simple add_items...")
    
    try:
        # Create session
        session_manager = get_session_manager()
        session_id = session_manager.new_session()
        print(f"✅ Created session: {session_id[:8]}...")
        
        # Get wrappers
        wrappers = get_function_wrappers(session_id)
        print("✅ Got function wrappers")
        
        # Try to add one item
        result = wrappers.add_items("3", [{"name": "test item", "description": "test description"}])
        print(f"📋 Add result: {result}")
        
        # Try to get bin contents
        result = wrappers.get_bin_contents("3")
        print(f"📋 Bin contents: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple_add()
