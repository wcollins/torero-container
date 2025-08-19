"""
Pytest configuration for torero-api tests
"""

import sys
from pathlib import Path

# Add the torero-api module to the Python path
project_root = Path(__file__).parent.parent
torero_api_path = project_root / "opt" / "torero-api"
sys.path.insert(0, str(torero_api_path))