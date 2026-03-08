"""Telegram bot entry point — registers all handlers and starts polling."""

import os
import socket
import sys

# Ensure the project directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import BotCommand
from telegram.error import NetworkError
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import (
    TELEGRAM_BOT_TOKEN, WORK_DIR, logger,
    POLLING_TIMEOUT, POLLING_READ_TIMEOUT, POLLING_CONNECT_TIMEOUT,
    POLLING_WRITE_TIMEOUT, POLLING_POOL_TIMEOUT, POLLING_INTERVAL,
    TCP_KEEPALIVE_IDLE,
)

# --- Handler imports (grouped by domain) ---

# Core
from handlers.start import start_handler, help_handler
from handlers.shell import shell_handler
from handlers.terminal import terminal_handler

# Claude AI
from handlers.claude import claude_handler, claude_continue_handler, chat_handler, exit_handler

# System & monitoring
from handlers.status import status_handler
from handlers.sysinfo import sysinfo_handler
from handlers.network import network_handler
from handlers.monitor import monitor_handler, monitor_refresh_callback
from handlers.app import app_handler
from handlers.steam import steam_handler
from handlers.tmux import tmux_handler

# Files & navigation
from handlers.cd import cd_handler, cd_callback_handler
from handlers.newproject import newproject_handler, pending_project_md_handler
from handlers.files import file_upload_handler
from handlers.getfile import getfile_handler


# --- Command menu (shown in Telegram's "/" autocomplete) ---

BOT_COMMANDS = [
    # Claude AI
    BotCommand("claude", "Run a one-shot Claude prompt"),
    BotCommand("chat", "Start interactive chat with Claude"),
    BotCommand("exit", "Exit interactive chat mode"),
    BotCommand("claude_continue", "Continue the last Claude conversation"),
    # Terminal & sessions
    BotCommand("t", "Manage terminal sessions"),
    BotCommand("tmux", "Manage tmux sessions"),
    # Files & navigation
    BotCommand("cd", "Change working directory"),
    BotCommand("newproject", "Create a new project"),
    BotCommand("getfile", "Download a file from server"),
    # System & monitoring
    BotCommand("status", "Show system status"),
    BotCommand("sysinfo", "Detailed system information"),
    BotCommand("network", "Show network diagnostics"),
    BotCommand("monitor", "Live screen monitor"),
    BotCommand("app", "Manage running applications"),
    BotCommand("steam", "Control Steam & Remote Play"),
    # Help
    BotCommand("help", "Show help message"),
]


def main():
    logger.info("Starting bot — working directory: %s", WORK_DIR)
    os.chdir(WORK_DIR)

    async def post_init(application):
        await application.bot.set_my_commands(BOT_COMMANDS)
        logger.info("Bot command menu registered")

    socket_opts = (
        (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
        (socket.IPPROTO_TCP, socket.TCP_KEEPALIVE, TCP_KEEPALIVE_IDLE),  # macOS
    )

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        # Polling (get_updates) timeouts + keepalive
        .get_updates_read_timeout(POLLING_READ_TIMEOUT)
        .get_updates_connect_timeout(POLLING_CONNECT_TIMEOUT)
        .get_updates_write_timeout(POLLING_WRITE_TIMEOUT)
        .get_updates_pool_timeout(POLLING_POOL_TIMEOUT)
        .get_updates_socket_options(socket_opts)
        # Regular API call timeouts + keepalive
        .read_timeout(POLLING_READ_TIMEOUT)
        .connect_timeout(POLLING_CONNECT_TIMEOUT)
        .write_timeout(POLLING_WRITE_TIMEOUT)
        .pool_timeout(POLLING_POOL_TIMEOUT)
        .socket_options(socket_opts)
        .build()
    )

    # --- Core ---
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))

    # --- Claude AI ---
    app.add_handler(CommandHandler("claude", claude_handler))
    app.add_handler(CommandHandler("claude_continue", claude_continue_handler))
    app.add_handler(CommandHandler("chat", chat_handler))
    app.add_handler(CommandHandler("exit", exit_handler))

    # --- Terminal & sessions ---
    app.add_handler(CommandHandler("t", terminal_handler))
    app.add_handler(CommandHandler("tmux", tmux_handler))

    # --- Files & navigation ---
    app.add_handler(CommandHandler("cd", cd_handler))
    app.add_handler(CommandHandler("newproject", newproject_handler))
    app.add_handler(CommandHandler("getfile", getfile_handler))

    # --- System & monitoring ---
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("sysinfo", sysinfo_handler))
    app.add_handler(CommandHandler("network", network_handler))
    app.add_handler(CommandHandler("monitor", monitor_handler))
    app.add_handler(CommandHandler("app", app_handler))
    app.add_handler(CommandHandler("steam", steam_handler))

    # --- Callback queries ---
    app.add_handler(CallbackQueryHandler(cd_callback_handler, pattern=r"^cd"))
    app.add_handler(CallbackQueryHandler(monitor_refresh_callback, pattern=r"^monitor_refresh$"))

    # --- File uploads (must be before the text catch-all) ---
    app.add_handler(MessageHandler(filters.Document.ALL, file_upload_handler))

    # --- Pending project.md input (group -1 so it runs before shell catch-all) ---
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        pending_project_md_handler,
    ), group=-1)

    # --- Plain text → shell command (catch-all, must be LAST) ---
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, shell_handler))

    async def error_handler(update, context):
        if isinstance(context.error, NetworkError):
            logger.warning("Network error (will auto-retry): %s", context.error)
        else:
            logger.error("Unhandled error: %s", context.error, exc_info=context.error)

    app.add_error_handler(error_handler)

    logger.info("Bot is polling...")
    app.run_polling(
        drop_pending_updates=True,
        timeout=POLLING_TIMEOUT,
        poll_interval=POLLING_INTERVAL,
    )


if __name__ == "__main__":
    main()
