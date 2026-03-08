"""Centralized configuration — split by concern, re-exported here.

Submodules:
    env.py          — Environment variables, paths, tokens
    commands.py     — Command allowlists, blocklists, validation rules
    security.py     — Sensitive paths, secret patterns, app allowlist
    claude.py       — Claude AI agent settings
    limits.py       — Timeouts, rate limits, size constraints
    logging_setup.py — Logging configuration and logger instance

All constants are re-exported from this package, so existing imports
like `from config import SAFE_COMMANDS` continue to work.
"""

# Environment (must load first — runs load_dotenv)
from config.env import *  # noqa: F401,F403

# Command rules
from config.commands import *  # noqa: F401,F403

# Security rules
from config.security import *  # noqa: F401,F403

# Steam configuration
from config.steam import *  # noqa: F401,F403

# Claude AI settings
from config.claude import *  # noqa: F401,F403

# Limits and timeouts
from config.limits import *  # noqa: F401,F403

# Logging (must load last — depends on env.LOG_FILE)
from config.logging_setup import *  # noqa: F401,F403
