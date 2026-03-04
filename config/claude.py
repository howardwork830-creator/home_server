"""Claude AI agent configuration."""

__all__ = ["CLAUDE_ALLOWED_TOOLS", "CLAUDE_SYSTEM_PROMPT", "CLAUDE_MAX_BUDGET_USD"]

CLAUDE_ALLOWED_TOOLS: str = (
    "Read,Glob,Grep,Edit,Write,"
    "Bash(git:*),Bash(python3:*),Bash(ls:*),Bash(cat:*)"
)

CLAUDE_SYSTEM_PROMPT: str = (
    "You are a coding assistant. "
    "Never read or modify files in ~/.ssh, ~/.aws, ~/.gnupg, ~/.config, or any .env file. "
    "Never run sudo, rm -rf, or any destructive command."
)

CLAUDE_MAX_BUDGET_USD: float = 1.0
