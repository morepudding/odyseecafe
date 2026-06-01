"""
Configuration helpers shared by OdyséeCafé scripts.
"""

import os


def openrouter_api_key() -> str:
    """Support both historical env var spellings used in the project."""
    return os.getenv("OPENROUTER_API_KEY") or os.getenv("OPEN_ROUTER_API_KEY", "")

