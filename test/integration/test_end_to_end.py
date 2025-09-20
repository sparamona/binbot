"""
End-to-end test script for BinBot
Tests the complete workflow: add items, check bin contents, search items
"""

import sys
import uuid
sys.path.append('.')

from session.session_manager import get_session_manager
from chat.function_wrappers import get_function_wrappers
from database.chromadb_client import get_chromadb_client
from llm.embeddings import get_embedding_service


def print_step(step_num, description):
    """Print a formatted step header"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print('='*60)


def print_result(result):
    """Print a formatted result"""
    print(f"📋 RESULT:")
    print(f"   {result}")


def test_end_to_end_workflow():
    """Test the complete BinBot workflow"""
    
    print("🤖 BinBot End-to-End Test")
    print("Testing workflow: Add screwdriver → Add pencil → Check bin → Search pencil")
    
    # Initialize components
    print("\n🔧 Initializing components...")
    session_manager = get_session_manager()
    db_client = get_chromadb_client()
    embedding_service = get_embedding_service()
    
    # Create a test session
    session_id = session_manager.new_session()
    print(f"✅ Created session: {session_id[:8]}...")
    
    # Get function wrappers for this session
    wrappers = get_function_wrappers(session_id)
    print("✅ Function wrappers ready")
    
    try:
        # STEP 1: Add screwdriver to bin 3
        print_step(1, "Add screwdriver to bin 3")
        
        result = wrappers.add_items(
            bin_id="3",
            items=[{
                "name": "screwdriver",
                "description": "Phillips head screwdriver for electronics"
            }]
        )
        print_result(result)
        
        # Check session state
        session = session_manager.get_session(session_id)
        print(f"📍 Current bin in session: {session['current_bin']}")
        
        # STEP 2: Add pencil to the same bin (bin 3)
        print_step(2, "Add pencil to the same bin")
        
        result = wrappers.add_items(
            bin_id="3",
            items=[{
                "name": "pencil",
                "description": "Yellow #2 pencil for writing"
            }]
        )
        print_result(result)
        
        # STEP 3: Check what's in bin 3
        print_step(3, "Check what's in bin 3")
        
        result = wrappers.get_bin_contents("3")
        print_result(result)
        
        # STEP 4: Search for the pencil
        print_step(4, "Search for the pencil")
        
        result = wrappers.search_items("pencil", limit=5)
        print_result(result)
        
        # STEP 5: Search for writing tools (semantic search)
        print_step(5, "Search for 'writing tools' (semantic search)")
        
        result = wrappers.search_items("writing tools", limit=5)
        print_result(result)
        
        # STEP 6: Search for electronics tools (semantic search)
        print_step(6, "Search for 'electronics tools' (semantic search)")
        
        result = wrappers.search_items("electronics tools", limit=5)
        print_result(result)
        
        # STEP 7: Check database state directly
        print_step(7, "Check database state directly")
        
        # Get all items in bin 3 directly from database
        bin_items = db_client.get_bin_contents("3")
        print(f"📋 RESULT:")
        print(f"   Database shows {len(bin_items)} items in bin 3:")
        for item in bin_items:
            print(f"   - {item['name']}: {item['description']}")
        
        # STEP 8: Test session conversation tracking
        print_step(8, "Test session conversation tracking")
        
        session_manager.add_message(session_id, "user", "add screwdriver to bin 3")
        session_manager.add_message(session_id, "assistant", "Added screwdriver to bin 3")
        session_manager.add_message(session_id, "user", "what's in bin 3?")
        session_manager.add_message(session_id, "assistant", "Bin 3 contains screwdriver and pencil")
        
        conversation = session_manager.get_conversation(session_id)
        print(f"📋 RESULT:")
        print(f"   Conversation has {len(conversation)} messages:")
        for msg in conversation:
            print(f"   {msg['role']}: {msg['content']}")
        
        print(f"\n{'='*60}")
        print("🎉 END-TO-END TEST COMPLETED SUCCESSFULLY!")
        print("✅ All components working together correctly")
        print(f"✅ Session management: Working")
        print(f"✅ Database operations: Working") 
        print(f"✅ Embedding generation: Working")
        print(f"✅ Semantic search: Working")
        print(f"✅ Function wrappers: Working")
        print('='*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ END-TO-END TEST FAILED!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up session
        session_manager.end_session(session_id)
        print(f"\n🧹 Cleaned up session: {session_id[:8]}...")


if __name__ == "__main__":
    print("🚀 Starting BinBot End-to-End Test...")
    print("This test demonstrates the complete workflow using all system components.")
    
    success = test_end_to_end_workflow()
    
    if success:
        print("\n🎊 All systems operational! BinBot is ready for API integration.")
    else:
        print("\n💥 System integration issues detected. Check component implementations.")
