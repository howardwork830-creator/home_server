"""Sensitive paths, secret patterns, and app allowlists."""

__all__ = [
    "BLOCKED_PATHS", "BLOCKED_PATH_PATTERNS",
    "SECRET_PATTERNS", "APP_LAUNCH_ALLOWLIST",
]

import re

# --- Sensitive paths ---
BLOCKED_PATHS: list[str] = [
    "~/.ssh/", "~/.aws/", "~/.gnupg/", "~/.docker/", "~/.config/",
    "~/.zshrc", "~/.bashrc", "~/.zsh_history", "~/.bash_history",
    "~/Library/Keychains/",
    "/etc/passwd", "/etc/shadow",
]
BLOCKED_PATH_PATTERNS: list[re.Pattern] = [
    re.compile(r"\.env\b"),  # any .env file
]

# --- Secret patterns for output scrubbing ---
SECRET_PATTERNS: list[re.Pattern] = [
    re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),           # Anthropic API keys
    re.compile(r"sk-[A-Za-z0-9]{20,}"),                  # OpenAI-style API keys
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),                 # GitHub PATs
    re.compile(r"xoxb-[A-Za-z0-9-]{20,}"),               # Slack bot tokens
    re.compile(r"\d{9,}:[A-Za-z0-9_-]{30,}"),            # Telegram bot tokens
    re.compile(r"(?i)^.*(PASSWORD|SECRET|TOKEN|KEY)\s*=\s*\S+", re.MULTILINE),
]

# --- App launch safety ---
APP_LAUNCH_ALLOWLIST: set[str] = {
    "Safari", "Finder", "Terminal", "Visual Studio Code",
    "Preview", "TextEdit", "Activity Monitor", "Console",
    "Music", "Photos", "Calculator", "Notes",
}
