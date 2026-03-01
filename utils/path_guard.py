import os
import shlex
from pathlib import Path

from config import BLOCKED_PATHS, BLOCKED_PATH_PATTERNS, logger


def _expand(p: str) -> str:
    """Expand ~ and resolve to absolute path."""
    return str(Path(os.path.expanduser(p)).resolve())


# Pre-expand blocked paths once at import time
_RESOLVED_BLOCKED: list[str] = [_expand(p.rstrip("/")) for p in BLOCKED_PATHS]
_RESOLVED_BLOCKED_DIRS: list[str] = [
    _expand(p.rstrip("/")) for p in BLOCKED_PATHS if p.endswith("/")
]


def check_path(path_str: str) -> str | None:
    """Check if a path string resolves to a sensitive location.

    Returns an error message if blocked, None if safe.
    """
    try:
        resolved = _expand(path_str)
    except (ValueError, OSError):
        return None  # can't resolve — not a real path, let it through

    # Check exact match or parent-of relationship for directory blocks
    for blocked_dir in _RESOLVED_BLOCKED_DIRS:
        if resolved == blocked_dir or resolved.startswith(blocked_dir + "/"):
            return f"Access to `{path_str}` is blocked (sensitive path)."

    # Check exact match for file blocks
    for blocked in _RESOLVED_BLOCKED:
        if resolved == blocked:
            return f"Access to `{path_str}` is blocked (sensitive path)."

    # Check pattern-based blocks (e.g. .env files)
    basename = os.path.basename(path_str)
    for pattern in BLOCKED_PATH_PATTERNS:
        if pattern.search(basename):
            return f"Access to `{path_str}` is blocked (matches sensitive pattern)."

    return None


def guard_command_paths(command: str) -> str | None:
    """Check all arguments in a command for sensitive paths.

    Returns an error message if any argument resolves to a blocked path, None if safe.
    """
    segments = command.split("|")
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        try:
            parts = shlex.split(segment)
        except ValueError:
            parts = segment.split()

        # Skip the command name itself, check arguments
        for arg in parts[1:]:
            if arg.startswith("-"):
                continue  # skip flags
            error = check_path(arg)
            if error:
                logger.info("Path guard blocked: %s in command: %s", arg, command)
                return error

    return None
