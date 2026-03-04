"""Shared utility modules.

    command_validator.py  — 7-layer command validation pipeline
    terminal_manager.py   — tmux session lifecycle (create, kill, run_in_session)
    subprocess_runner.py  — Async shell execution with timeout + output cap
    path_guard.py         — Sensitive path blocking
    scrubber.py           — Secret redaction from output
    rate_limiter.py       — Sliding window rate limiter
    chunker.py            — Split text for Telegram's message limit
    claude_stream.py      — Parse Claude CLI stream-json output
    audit.py              — Structured JSONL audit logging
"""
