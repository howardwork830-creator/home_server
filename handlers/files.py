from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from config import MAX_UPLOAD_SIZE, WORK_DIR, logger
from handlers.auth import authorized


@authorized
async def file_upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if document is None:
        return

    # Size check
    if document.file_size and document.file_size > MAX_UPLOAD_SIZE:
        await update.message.reply_text(
            f"File too large ({document.file_size // (1024*1024)}MB). "
            f"Max is {MAX_UPLOAD_SIZE // (1024*1024)}MB."
        )
        return

    # Sanitize filename — strip path traversal, prefix dotfiles
    raw_name = document.file_name or "upload"
    safe_name = Path(raw_name).name
    if safe_name.startswith("."):
        safe_name = "_" + safe_name

    dest = WORK_DIR / safe_name

    logger.info(
        "File upload from %s: %s -> %s",
        update.effective_user.id, raw_name, dest,
    )

    tg_file = await document.get_file()
    await tg_file.download_to_drive(str(dest))

    await update.message.reply_text(f"Saved to `{dest}`", parse_mode="Markdown")
