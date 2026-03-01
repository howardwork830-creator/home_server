import os
import sys

# Ensure the project directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from config import TELEGRAM_BOT_TOKEN, WORK_DIR, logger
from handlers.start import start_handler, help_handler
from handlers.shell import shell_handler
from handlers.claude import claude_handler, claude_continue_handler
from handlers.files import file_upload_handler
from handlers.status import status_handler
from handlers.tmux import tmux_handler


def main():
    logger.info("Starting bot — working directory: %s", WORK_DIR)
    os.chdir(WORK_DIR)

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("claude", claude_handler))
    app.add_handler(CommandHandler("claude_continue", claude_continue_handler))
    app.add_handler(CommandHandler("tmux", tmux_handler))

    # File uploads (must be before the text catch-all)
    app.add_handler(MessageHandler(filters.Document.ALL, file_upload_handler))

    # Plain text → shell command (catch-all, must be last)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, shell_handler))

    logger.info("Bot is polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
