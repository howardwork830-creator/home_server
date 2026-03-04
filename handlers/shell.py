"""Shell command handler — routes plain text messages.

Handles keyboard button hints, chat mode routing, exit commands,
and executes validated commands in persistent terminal sessions.
"""

import time

from telegram import Update
from telegram.ext import ContextTypes

from config import logger
from handlers.auth import authorized
from handlers.cd import get_working_dir
from handlers.claude import is_chat_mode, chat_message_handler
from handlers.newproject import pending_project_md_handler
from handlers.terminal import (
    _get_active,
    _get_terminals,
    close_terminal,
    ensure_terminal,
)
from utils.audit import log_action
from utils.chunker import chunk_text
from utils.command_validator import validate_command
from utils.rate_limiter import rate_limiter
from utils.scrubber import scrub_output
from utils.terminal_manager import run_in_session

# Keyboard button → hint text mapping
BUTTON_HINTS = {
    "Shell": "Type any allowlisted command (e.g. `ls`, `pwd`, `uptime`).",
    "Claude": "Use /claude <prompt> to ask Claude a question.",
    "Files": "Upload a document to save it to the working directory.",
    "Git": "Type a git command (e.g. `git status`, `git log`).",
    "Status": "Use /status to see system info.",
    "Terminal": "Use /t to manage terminals. Commands auto-create a terminal.",
    "tmux": "Use /tmux ls or /tmux send <session> <cmd>.",
    "CD": "Use /cd to select a project directory on Desktop.",
    "Chat": "Use /chat to enter Claude chat mode for back-and-forth coding.",
    "New Project": "Use /newproject <name> to create a new project folder on Desktop.",
    "Network": "Use /network to see network diagnostics (IPs, connectivity, VPN).",
    "Get File": "Use /getfile <path> to download a file.",
    "App": "Use /app to list, launch, or quit applications.",
    "Sys Info": "Use /sysinfo for detailed system information.",
}


@authorized
async def shell_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text.strip()
    if not command:
        return

    user_id = update.effective_user.id

    # Handle keyboard button presses
    if command in BUTTON_HINTS:
        await update.message.reply_text(BUTTON_HINTS[command])
        return

    # Pending project.md — intercept before chat mode and shell
    if context.user_data.get("pending_project_md"):
        await pending_project_md_handler(update, context)
        return

    # Chat mode — route to Claude instead of shell
    if is_chat_mode(context):
        await chat_message_handler(update, context)
        return

    # Rate limit check
    limit_msg = rate_limiter.check(user_id, "shell")
    if limit_msg:
        await update.message.reply_text(limit_msg)
        return

    # Handle "exit" — close active terminal
    if command == "exit":
        terminals = _get_terminals(context)
        active = _get_active(context)
        if active and active in terminals:
            await close_terminal(user_id, active, context)
            new_active = _get_active(context)
            if new_active:
                await update.message.reply_text(
                    f"Closed terminal {active}. Active terminal: {new_active}"
                )
            else:
                await update.message.reply_text(
                    f"Closed terminal {active}. No active terminals."
                )
            return
        await update.message.reply_text("No active terminal to close.")
        return

    # Validate command through security pipeline
    error = validate_command(command)
    if error:
        logger.info("Blocked command from %s: %s — %s", user_id, command, error)
        log_action(user_id, "shell", command, result="blocked")
        await update.message.reply_text(f"Blocked: {error}")
        return

    # Run in persistent terminal session
    try:
        slot, tmux_session = await ensure_terminal(user_id, context)
    except RuntimeError as e:
        await update.message.reply_text(str(e))
        return

    logger.info("Running command from %s in T%d: %s", user_id, slot, command)
    start_time = time.monotonic()
    output, return_code = await run_in_session(tmux_session, command)
    duration = time.monotonic() - start_time

    # Scrub secrets from output
    output = scrub_output(output)

    terminals = _get_terminals(context)
    t_info = terminals.get(slot, {})
    t_name = t_info.get("name", f"T{slot}")
    t_label = f"[T{slot}: {t_name}] " if t_name != f"T{slot}" else f"[T{slot}] "

    prefix = t_label if return_code == 0 else f"{t_label}[exit {return_code}]\n"
    full_output = prefix + output

    result = "ok" if return_code == 0 else f"exit_{return_code}"
    log_action(user_id, "shell", command, result=result, duration_s=duration)

    for chunk in chunk_text(full_output):
        await update.message.reply_text(f"```\n{chunk}\n```", parse_mode="Markdown")
