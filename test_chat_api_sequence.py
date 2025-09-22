#!/usr/bin/env python3
"""
Test the /chat API with the requested sequence:
1. List contents of bin 3
2. Add a random object to bin 3
3. Ask chat to remove it
4. List contents again to confirm removal
5. Show complete conversation history

This version tests the components directly without requiring a running server.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set memory mode for clean testing
os.environ['STORAGE_MODE'] = 'memory'

from session.session_manager import get_session_manager
from chat.function_wrappers import get_function_wrappers
from llm.client import get_gemini_client
from typing import Dict, Any

class ChatAPITester:
    def __init__(self):
        self.session_manager = get_session_manager()
        self.session_id = None
        self.llm_client = get_gemini_client()

    def start_session(self) -> bool:
        """Create a new session"""
        try:
            self.session_id = self.session_manager.new_session()
            print(f"✅ Session started: {self.session_id[:8]}...")
            return True
        except Exception as e:
            print(f"❌ Failed to start session: {e}")
            return False
    
    def send_chat_message(self, message: str) -> Dict[str, Any]:
        """Send a message to the chat system (simulating the API)"""
        if not self.session_id:
            raise Exception("No active session")

        try:
            # Add user message to conversation (like the API does)
            full_message = message + "\n\n The contents of any bin change at any time without your knowledge.  Remember to abide by system instructions.  " \
                          "Always use the tools provided whenever possible.  Never rely on your memory for bin contents.  ALWAYS use get_bin_contents to retrieve the contents of a bin."

            self.session_manager.add_message(self.session_id, "user", full_message)

            # Get conversation history
            conversation = self.session_manager.get_conversation(self.session_id)

            # Convert to LLM format
            messages = []
            for msg in conversation:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # Get function wrappers for this session
            wrappers = get_function_wrappers(self.session_id)

            # Create function mapping
            function_mapping = {
                "add_items": wrappers.add_items,
                "search_items": wrappers.search_items,
                "get_bin_contents": wrappers.get_bin_contents,
                "move_items": wrappers.move_items,
                "remove_items": wrappers.remove_items
            }

            # Send to LLM with function calling (tools should be a list, not dict)
            tools = list(function_mapping.values())
            response_text = self.llm_client.chat_completion(messages, tools)

            # Add model response to conversation
            self.session_manager.add_message(self.session_id, "model", response_text)

            # Get current bin from session
            updated_session = self.session_manager.get_session(self.session_id)
            current_bin = updated_session.get('current_bin') if updated_session else None

            print(f"✅ Chat response received")
            return {"success": True, "response": response_text, "current_bin": current_bin}

        except Exception as e:
            print(f"❌ Chat error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "response": f"Error: {e}"}
    
    def get_conversation_history(self) -> list:
        """Get the conversation history from session"""
        if not self.session_id:
            return []

        try:
            return self.session_manager.get_conversation(self.session_id)
        except Exception as e:
            print(f"❌ Error getting conversation: {e}")
            return []
    
    def run_test_sequence(self):
        """Run the complete test sequence"""
        print("🚀 Starting Chat API Test Sequence")
        print("=" * 50)
        
        # Start session
        if not self.start_session():
            return False
        
        print("\n📋 Step 1: List contents of bin 3")
        print("-" * 30)
        response1 = self.send_chat_message("List the contents of bin 3")
        print(f"Response: {response1.get('response', 'No response')}")
        
        print("\n📦 Step 2: Add a random object to bin 3")
        print("-" * 30)
        response2 = self.send_chat_message("Add a red screwdriver to bin 3")
        print(f"Response: {response2.get('response', 'No response')}")
        
        print("\n🗑️ Step 3: Ask chat to remove the item")
        print("-" * 30)
        response3 = self.send_chat_message("Remove the red screwdriver from bin 3")
        print(f"Response: {response3.get('response', 'No response')}")
        
        print("\n📋 Step 4: List contents again to confirm removal")
        print("-" * 30)
        response4 = self.send_chat_message("List the contents of bin 3 again")
        print(f"Response: {response4.get('response', 'No response')}")
        
        print("\n💬 Step 5: Complete Conversation History")
        print("=" * 50)
        conversation = self.get_conversation_history()
        
        if conversation:
            print("📜 Conversation History (as would be sent to LLM):")
            print("-" * 50)
            for i, msg in enumerate(conversation, 1):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                timestamp = msg.get('timestamp', '')
                
                print(f"\n{i}. [{role.upper()}] ({timestamp})")
                print(f"   {content}")
                print("-" * 50)
        else:
            print("❌ No conversation history available")
        
        return True

def main():
    """Main entry point"""
    print("🧪 Testing Chat API Components Directly")
    print("(No server required - testing components in-memory)")
    print()

    # Run the test
    tester = ChatAPITester()
    success = tester.run_test_sequence()

    if success:
        print("\n🎉 Test sequence completed!")
        return 0
    else:
        print("\n❌ Test sequence failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
