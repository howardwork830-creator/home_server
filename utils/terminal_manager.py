"""Stateless helpers for managing tmux-backed terminal sessions."""

import asyncio
import os
import uuid

from config import COMMAND_TIMEOUT, MAX_OUTPUT_BYTES, logger


def _session_name(user_id: int, slot: int) -> str:
    return f"tg_{user_id}_{slot}"


async def create_session(user_id: int, slot: int, cwd: str) -> str:
    """Create a new tmux session and return its name."""
    name = _session_name(user_id, slot)
    proc = await asyncio.create_subprocess_exec(
        "tmux", "new-session", "-d", "-s", name, "-x", "200", "-y", "50",
        cwd=cwd,
    )
    await proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to create tmux session {name}")
    return name


async def kill_session(session_name: str) -> None:
    """Kill a tmux session."""
    proc = await asyncio.create_subprocess_exec(
        "tmux", "kill-session", "-t", session_name,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()


async def session_exists(session_name: str) -> bool:
    """Check if a tmux session exists."""
    proc = await asyncio.create_subprocess_exec(
        "tmux", "has-session", "-t", session_name,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()
    return proc.returncode == 0


async def run_in_session(
    session_name: str,
    command: str,
    timeout: int = COMMAND_TIMEOUT,
) -> tuple[str, int]:
    """Run a command in a tmux session using file-based output capture.

    Returns (output, return_code).
    """
    tag = uuid.uuid4().hex[:12]
    out_file = f"/tmp/tg_out_{tag}"
    rc_file = f"/tmp/tg_out_{tag}.rc"

    # Wrap command: redirect output, write exit code, signal completion
    wrapped = (
        f"{command} > {out_file} 2>&1; "
        f"echo $? > {rc_file}; "
        f"tmux wait-for -S {tag}"
    )

    # Send wrapped command to tmux pane
    send_proc = await asyncio.create_subprocess_exec(
        "tmux", "send-keys", "-t", session_name, wrapped, "Enter",
    )
    await send_proc.wait()

    # Wait for command to finish (tmux wait-for blocks until signaled)
    try:
        wait_proc = await asyncio.create_subprocess_exec(
            "tmux", "wait-for", tag,
        )
        await asyncio.wait_for(wait_proc.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("Terminal command timed out after %ds: %s", timeout, command)
        # Clean up
        _cleanup(out_file, rc_file)
        return (f"Command timed out after {timeout}s.", -1)

    # Read output
    try:
        with open(out_file, "rb") as f:
            raw = f.read(MAX_OUTPUT_BYTES + 1)
        truncated = len(raw) > MAX_OUTPUT_BYTES
        if truncated:
            raw = raw[:MAX_OUTPUT_BYTES]
        output = raw.decode("utf-8", errors="replace").strip()
        if truncated:
            output += f"\n\n[Output truncated at {MAX_OUTPUT_BYTES // 1024}KB]"
    except FileNotFoundError:
        output = "(no output)"

    # Read exit code
    try:
        with open(rc_file, "r") as f:
            return_code = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return_code = -1

    _cleanup(out_file, rc_file)
    return (output or "(no output)", return_code)


def _cleanup(*paths: str) -> None:
    for p in paths:
        try:
            os.remove(p)
        except OSError:
            pass
