"""Logging configuration — sets up file + console handlers."""

__all__ = ["LOG_LEVEL", "logger"]

import logging
import os

from config.env import LOG_FILE

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
