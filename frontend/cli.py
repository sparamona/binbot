#!/usr/bin/env python3
"""
BinBot CLI Frontend
Text-based interface for BinBot inventory management system
"""

import requests
import json
import os
import sys
from pathlib import Path
from typing import Optional


class BinBotCLI:
    """Command-line interface for BinBot"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session_id: Optional[str] = None
        self.running = True
        
    def start_session(self) -> bool:
        """Create a new session with the API"""
        try:
            response = requests.post(f"{self.base_url}/api/session")
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get('session_id')
                print(f"✅ Session started: {self.session_id[:8]}...")
                return True
            else:
                print(f"❌ Failed to start session: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def end_session(self) -> bool:
        """End the current session"""
        if not self.session_id:
            return True
            
        try:
            response = requests.delete(f"{self.base_url}/api/session/{self.session_id}")
            if response.status_code == 200:
                print("✅ Session ended")
                return True
            else:
                print(f"⚠️ Session cleanup failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"⚠️ Session cleanup error: {e}")
            return False
    
    def send_command(self, command: str) -> bool:
        """Send a text command to the chat API"""
        if not self.session_id:
            print("❌ No active session")
            return False
            
        try:
            headers = {'Cookie': f'session_id={self.session_id}'}
            data = {'message': command}

            response = requests.post(
                f"{self.base_url}/api/chat/command",
                json=data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"🤖 {result.get('response', 'No response')}")
                return True
            else:
                print(f"❌ Command failed: {response.status_code}")
                if response.text:
                    print(f"   Error: {response.text}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def upload_image(self, image_path: str) -> bool:
        """Upload an image to the chat API"""
        if not self.session_id:
            print("❌ No active session")
            return False
            
        # Check if file exists
        if not os.path.exists(image_path):
            print(f"❌ Image file not found: {image_path}")
            return False
            
        try:
            headers = {'Cookie': f'session_id={self.session_id}'}
            
            with open(image_path, 'rb') as f:
                files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}

                response = requests.post(
                    f"{self.base_url}/api/chat/image",
                    files=files,
                    headers=headers
                )
            
            if response.status_code == 200:
                result = response.json()
                print(f"📸 Image uploaded successfully")
                print(f"🤖 {result.get('response', 'No response')}")
                return True
            else:
                print(f"❌ Image upload failed: {response.status_code}")
                if response.text:
                    print(f"   Error: {response.text}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def show_help(self):
        """Show available commands"""
        print("\n📋 BinBot CLI Commands:")
        print("  /help                     - Show this help message")
        print("  /upload <path>            - Upload an image file")
        print("  /quit, /exit, /q          - Exit the application")
        print("  <any text>                - Send command to BinBot")
        print("\n💡 Examples:")
        print("  add screwdriver to bin A")
        print("  what's in bin B?")
        print("  /upload photo.jpg")
        print("  search for red items")
        print()
    
    def run(self):
        """Main application loop"""
        print("🤖 BinBot CLI Frontend")
        print("=" * 30)
        
        # Start session
        if not self.start_session():
            print("Failed to connect to BinBot API")
            return
        
        print("Type '/help' for commands or '/quit' to exit")
        print()
        
        try:
            while self.running:
                try:
                    # Get user input
                    user_input = input("🔧 > ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Check if it's a CLI command (starts with /)
                    if user_input.startswith('/'):
                        parts = user_input[1:].split()  # Remove the / and split
                        command = parts[0].lower()

                        if command in ['quit', 'exit', 'q']:
                            self.running = False

                        elif command == 'help':
                            self.show_help()

                        elif command == 'upload':
                            if len(parts) < 2:
                                print("❌ Usage: /upload <image_path>")
                            else:
                                image_path = parts[1]
                                self.upload_image(image_path)
                        else:
                            print(f"❌ Unknown command: /{command}")
                            print("   Type '/help' for available commands")
                            
                    else:
                        # Send as regular command
                        self.send_command(user_input)
                        
                except KeyboardInterrupt:
                    print("\n\n👋 Interrupted by user")
                    self.running = False
                    
                except EOFError:
                    print("\n\n👋 EOF received")
                    self.running = False
                    
        finally:
            # Clean up session
            self.end_session()
            print("👋 Goodbye!")


def main():
    """Main entry point"""
    # Check if API server URL is provided
    api_url = os.environ.get('BINBOT_API_URL', 'http://localhost:8000')
    
    if len(sys.argv) > 1:
        api_url = sys.argv[1]
    
    # Create and run CLI
    cli = BinBotCLI(api_url)
    cli.run()


if __name__ == "__main__":
    main()
