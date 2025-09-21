#!/usr/bin/env python3
"""
BinBot CLI Runner
Convenience script to run the BinBot CLI frontend
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run CLI
from frontend.cli import main

if __name__ == "__main__":
    main()
