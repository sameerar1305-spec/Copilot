"""
MindGuard App Launcher
Run this file to start the mobile application.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from health_tracker.main import main

if __name__ == "__main__":
    main()
