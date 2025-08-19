#!/usr/bin/env python3
"""
Script to run the torero API server.

This script provides a convenient way to start the torero API server
without having to use the "python -m torero_api" command.
"""

import sys
import os

# Add parent directory to python path to allow importing torero_api
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, parent_dir)

# Import main function from the torero_api module
from torero_api.__main__ import main

if __name__ == "__main__":
    main()