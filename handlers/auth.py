import functools

from telegram import Update
from telegram.ext import ContextTypes

from config import AUTHORIZED_USER_IDS, logger
from utils.audit import log_action


def authorized(func):
    """Decorator that restricts handler to authorized user IDs."""

    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user is None or user.id not in AUTHORIZED_USER_IDS:
            uid = user.id if user else 0
            logger.warning("Unauthorized access attempt from user %s", uid)
            log_action(uid, "unauthorized", result="denied")
            await update.message.reply_text("Access denied.")
            return
        return await func(update, context)

    return wrapper
