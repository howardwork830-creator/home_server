from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from config import MAX_UPLOAD_SIZE, logger
from handlers.auth import authorized
from handlers.cd import get_working_dir
from utils.audit import log_action
from utils.path_guard import check_path


@authorized
async def getfile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /getfile <path> — send a file from the server to Telegram."""
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("Usage: /getfile <path>")
        return

    raw_path = " ".join(context.args)

    # Resolve relative paths against working directory
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path(get_working_dir(context)) / raw_path
    path = path.resolve()

    # Security: path guard blocks sensitive locations
    err = check_path(str(path))
    if err:
        log_action(user_id, "getfile", prompt=raw_path, result="blocked")
        await update.message.reply_text(f"Blocked: {err}")
        return

    # Must exist and be a regular file
    if not path.exists():
        await update.message.reply_text(f"File not found: `{raw_path}`", parse_mode="Markdown")
        return

    if not path.is_file():
        await update.message.reply_text("Cannot download directories. Specify a file path.")
        return

    # Size check
    size = path.stat().st_size
    if size > MAX_UPLOAD_SIZE:
        await update.message.reply_text(
            f"File too large ({size // (1024 * 1024)}MB). "
            f"Max is {MAX_UPLOAD_SIZE // (1024 * 1024)}MB."
        )
        return

    logger.info("Sending file to %s: %s (%d bytes)", user_id, path, size)
    log_action(user_id, "getfile", prompt=raw_path, result="ok")

    with open(path, "rb") as f:
        await update.message.reply_document(document=f, filename=path.name)
