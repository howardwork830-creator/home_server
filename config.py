import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
AUTHORIZED_USER_IDS: set[int] = {
    int(uid.strip())
    for uid in os.environ["AUTHORIZED_USER_IDS"].split(",")
    if uid.strip()
}

# --- Paths ---
WORK_DIR = Path(os.getenv("WORK_DIR", str(Path(__file__).parent)))
LOG_FILE = os.getenv("LOG_FILE", str(WORK_DIR / "bot.log"))

# --- Command safety ---
SAFE_COMMANDS: set[str] = {
    "ls", "pwd", "cat", "head", "tail", "grep", "find", "ps", "df",
    "uptime", "echo", "wc", "sort", "tree", "which", "file", "du",
    "date", "whoami", "python3", "git", "tmux", "tailscale", "claude",
}

DANGEROUS_PATTERNS: list[re.Pattern] = [
    re.compile(r"\brm\s+(-\w*r\w*f|--recursive|--force)\b", re.IGNORECASE),
    re.compile(r"\bsudo\b"),
    re.compile(r"\bmkfs\b"),
    re.compile(r"\bchmod\s+777\b"),
    re.compile(r"\breboot\b"),
    re.compile(r"\bshutdown\b"),
    re.compile(r"\bdd\b\s+if="),
    re.compile(r"curl\s.*\|\s*sh"),
    re.compile(r"wget\s.*\|\s*sh"),
    re.compile(r"\bkill\s+-9\b"),
    re.compile(r"\blaunchctl\b"),
    re.compile(r"\brm\s+-rf\b"),
]

# --- Shell metacharacter blocking ---
# These bypass pipe-only parsing and have no legitimate use in allowlisted commands
SHELL_METACHARACTERS: list[str] = [";", "&&", "||", "$(", "`", "<(", ">(", "\n"]

# --- Argument injection defense ---
# Per-command blocked argument patterns
DANGEROUS_ARGS: dict[str, list[str]] = {
    "find": ["-exec", "-execdir", "-delete", "-ok"],
    "sort": ["--compress-prog"],
    "grep": ["--pre"],
    "python3": ["-c"],
}

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

# --- Timeouts & limits ---
COMMAND_TIMEOUT = 30
TAILSCALE_STATUS_TIMEOUT = 5
CLAUDE_TIMEOUT = 300
TELEGRAM_CHUNK_SIZE = 4000
MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB
MAX_OUTPUT_BYTES = 50 * 1024  # 50 KB output cap

# --- Rate limits ---
RATE_LIMIT_SHELL = 20   # commands per minute
RATE_LIMIT_CLAUDE = 5   # requests per minute
RATE_LIMIT_WINDOW = 60  # sliding window in seconds

# --- Git ---
ALLOWED_GIT_SUBCOMMANDS: set[str] = {
    "status", "add", "commit", "push", "log", "diff", "branch",
}

# --- Claude agent mode ---
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

# --- Audit ---
AUDIT_LOG_FILE = str(WORK_DIR / "audit.jsonl")

# --- Secret patterns for output scrubbing ---
SECRET_PATTERNS: list[re.Pattern] = [
    re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),           # Anthropic API keys
    re.compile(r"sk-[A-Za-z0-9]{20,}"),                  # OpenAI-style API keys
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),                 # GitHub PATs
    re.compile(r"xoxb-[A-Za-z0-9-]{20,}"),               # Slack bot tokens
    re.compile(r"\d{9,}:[A-Za-z0-9_-]{30,}"),            # Telegram bot tokens
    re.compile(r"(?i)^.*(PASSWORD|SECRET|TOKEN|KEY)\s*=\s*\S+", re.MULTILINE),  # env-style secrets
]

# --- Logging ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("telegram_bot")
