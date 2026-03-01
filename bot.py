import os
import sys

# Ensure the project directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import BotCommand
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from config import TELEGRAM_BOT_TOKEN, WORK_DIR, logger
from handlers.cd import cd_handler, cd_callback_handler
from handlers.claude import claude_handler, claude_continue_handler, chat_handler, exit_handler
from handlers.files import file_upload_handler
from handlers.newproject import newproject_handler
from handlers.shell import shell_handler
from handlers.start import start_handler, help_handler
from handlers.status import status_handler
from handlers.tmux import tmux_handler

BOT_COMMANDS = [
    BotCommand("claude", "Run a one-shot Claude prompt"),
    BotCommand("chat", "Start interactive chat with Claude"),
    BotCommand("exit", "Exit interactive chat mode"),
    BotCommand("claude_continue", "Continue the last Claude conversation"),
    BotCommand("cd", "Change working directory"),
    BotCommand("newproject", "Create a new project"),
    BotCommand("tmux", "Manage tmux sessions"),
    BotCommand("status", "Show system status"),
    BotCommand("help", "Show help message"),
]


def main():
    logger.info("Starting bot — working directory: %s", WORK_DIR)
    os.chdir(WORK_DIR)

    async def post_init(application):
        await application.bot.set_my_commands(BOT_COMMANDS)
        logger.info("Bot command menu registered")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("claude", claude_handler))
    app.add_handler(CommandHandler("claude_continue", claude_continue_handler))
    app.add_handler(CommandHandler("tmux", tmux_handler))
    app.add_handler(CommandHandler("chat", chat_handler))
    app.add_handler(CommandHandler("exit", exit_handler))
    app.add_handler(CommandHandler("cd", cd_handler))
    app.add_handler(CommandHandler("newproject", newproject_handler))
    app.add_handler(CallbackQueryHandler(cd_callback_handler, pattern=r"^cd"))

    # File uploads (must be before the text catch-all)
    app.add_handler(MessageHandler(filters.Document.ALL, file_upload_handler))

    # Plain text → shell command (catch-all, must be last)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, shell_handler))

    logger.info("Bot is polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
