"""Command validation pipeline — 7-layer security check.

Validates shell commands before execution:
    1. Block shell metacharacters
    2. Block dangerous patterns (regex)
    3. Block sensitive paths
    4. Parse pipe segments, check allowlist
    5. Block dangerous arguments per command
    6. Enforce required arguments (prevent hangs)
    7. Validate subcommands/flags
"""

import shlex

from config import (
    DANGEROUS_ARGS,
    DANGEROUS_PATTERNS,
    REQUIRED_ARGS,
    SAFE_COMMANDS,
    SHELL_METACHARACTERS,
    SUBCOMMAND_ALLOWLISTS,
)
from utils.path_guard import guard_command_paths


def _check_metacharacters(command: str) -> str | None:
    """Block shell metacharacters that bypass pipe-only parsing."""
    for meta in SHELL_METACHARACTERS:
        if meta in command:
            return f"Blocked: shell metacharacter `{meta}` is not allowed."
    return None


def _check_dangerous_args(base_cmd: str, parts: list[str]) -> str | None:
    """Block known dangerous arguments for specific commands."""
    blocked = DANGEROUS_ARGS.get(base_cmd)
    if not blocked:
        return None
    for arg in parts[1:]:
        for bad in blocked:
            if arg == bad or arg.startswith(bad + "=") or arg.startswith(bad + " "):
                return f"Blocked: argument `{arg}` is not allowed for `{base_cmd}`."
    return None


def _check_required_args(base_cmd: str, parts: list[str]) -> str | None:
    """Ensure commands that need specific flags have them (prevents hangs)."""
    req = REQUIRED_ARGS.get(base_cmd)
    if not req:
        return None
    flag = req["flag"]
    if not any(arg == flag or arg.startswith(flag) for arg in parts[1:]):
        return req["error"]
    return None


def validate_command(command: str) -> str | None:
    """Validate a command string through 7 security layers.

    Returns an error message if blocked, None if the command is safe to run.
    """
    # 1. Metacharacter blocking
    meta_err = _check_metacharacters(command)
    if meta_err:
        return meta_err

    # 2. Dangerous pattern check
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return f"Blocked: matches dangerous pattern `{pattern.pattern}`"

    # 3. Path guard — check for sensitive paths in arguments
    path_err = guard_command_paths(command)
    if path_err:
        return path_err

    # 4. Parse pipe segments and validate each command
    segments = command.split("|")
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        try:
            parts = shlex.split(segment)
        except ValueError:
            parts = segment.split()

        if not parts:
            continue

        base_cmd = parts[0]
        if base_cmd not in SAFE_COMMANDS:
            return f"Command `{base_cmd}` is not in the allowlist."

        # 5. Argument injection defense
        arg_err = _check_dangerous_args(base_cmd, parts)
        if arg_err:
            return arg_err

        # 6. Required args check (prevent hangs)
        req_err = _check_required_args(base_cmd, parts)
        if req_err:
            return req_err

        # 7. Subcommand/flag allowlist validation
        if base_cmd in SUBCOMMAND_ALLOWLISTS:
            if len(parts) < 2:
                return f"`{base_cmd}` requires a subcommand or flag."
            if parts[1] not in SUBCOMMAND_ALLOWLISTS[base_cmd]:
                return (
                    f"`{base_cmd}` subcommand `{parts[1]}` is not allowed. "
                    f"Allowed: {', '.join(sorted(SUBCOMMAND_ALLOWLISTS[base_cmd]))}"
                )

    return None
