"""Environment variables and paths — loaded from .env file."""

__all__ = [
    "TELEGRAM_BOT_TOKEN", "AUTHORIZED_USER_IDS",
    "WORK_DIR", "LOG_FILE",
    "SCREEN_STREAM_PORT", "GO2RTC_HOST", "MINIAPP_BASE_URL",
    "AUDIT_LOG_FILE",
]

import os
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
WORK_DIR = Path(os.getenv("WORK_DIR", str(Path(__file__).resolve().parent.parent)))
LOG_FILE = os.getenv("LOG_FILE", str(WORK_DIR / "bot.log"))

# --- Monitor / Live Stream ---
SCREEN_STREAM_PORT = int(os.getenv("SCREEN_STREAM_PORT", "9999"))
GO2RTC_HOST = os.getenv("GO2RTC_HOST", "")
MINIAPP_BASE_URL = os.getenv("MINIAPP_BASE_URL", "")

# --- Audit ---
AUDIT_LOG_FILE = str(WORK_DIR / "audit.jsonl")
