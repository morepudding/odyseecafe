"""
Configuration helpers shared by OdyséeCafé scripts.
"""

import os


def env_value(name: str, default: str = "") -> str:
    """Read Vercel/local env values defensively; pasted secrets may contain CRLF."""
    return (os.getenv(name) or default).strip().strip('"').strip("'")


def openrouter_api_key() -> str:
    """Support both historical env var spellings used in the project."""
    return env_value("OPENROUTER_API_KEY") or env_value("OPEN_ROUTER_API_KEY")


def supabase_url() -> str:
    return env_value("SUPABASE_URL")


def supabase_key() -> str:
    """Server-side Supabase key. Prefer service role for private RAG tables."""
    return (
        env_value("SUPABASE_SERVICE_ROLE_KEY")
        or env_value("SUPABASE_KEY")
        or env_value("SUPABASE_ANON_KEY")
    )
