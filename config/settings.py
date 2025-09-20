"""
BinBot Configuration - Simple environment variable based settings
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Simple configuration constants
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DATABASE_PATH = os.getenv('DATABASE_PATH', './data/chromadb')
IMAGES_PATH = os.getenv('IMAGES_PATH', './data/images')
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', '8000'))
SESSION_TTL_MINUTES = int(os.getenv('SESSION_TTL_MINUTES', '30'))

# Storage mode: 'memory' for testing, 'persistent' for production
STORAGE_MODE = os.getenv('STORAGE_MODE', 'persistent')
