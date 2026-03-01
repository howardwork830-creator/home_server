import shlex
import time

from telegram import Update
from telegram.ext import ContextTypes

from config import (
    DANGEROUS_ARGS,
    DANGEROUS_PATTERNS,
    SAFE_COMMANDS,
    ALLOWED_GIT_SUBCOMMANDS,
    SHELL_METACHARACTERS,
    logger,
)
from handlers.auth import authorized
from handlers.cd import get_working_dir
from handlers.claude import is_chat_mode, chat_message_handler
from handlers.newproject import pending_project_md_handler
from utils.audit import log_action
from utils.chunker import chunk_text
from utils.path_guard import guard_command_paths
from utils.rate_limiter import rate_limiter
from utils.scrubber import scrub_output
from utils.subprocess_runner import run_shell_command


def _check_metacharacters(command: str) -> str | None:
    """Block shell metacharacters that bypass pipe-only parsing."""
    for meta in SHELL_METACHARACTERS:
        if meta in command:
            return f"Blocked: shell metacharacter `{meta}` is not allowed."
    return None


def _check_dangerous_args(base_cmd: str, parts: list[str]) -> str | None:
    """Block known dangerous arguments for specific commands."""
    blocked = DANGEROUS_ARGS.get(base_cmd)
    if not blocked:
        return None
    for arg in parts[1:]:
        for bad in blocked:
            if arg == bad or arg.startswith(bad + "=") or arg.startswith(bad + " "):
                return f"Blocked: argument `{arg}` is not allowed for `{base_cmd}`."
    return None


def validate_command(command: str) -> str | None:
    """Validate a command string. Returns an error message or None if valid."""
    # 1. Metacharacter blocking
    meta_err = _check_metacharacters(command)
    if meta_err:
        return meta_err

    # 2. Dangerous pattern check
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return f"Blocked: matches dangerous pattern `{pattern.pattern}`"

    # 3. Path guard — check for sensitive paths in arguments
    path_err = guard_command_paths(command)
    if path_err:
        return path_err

    # 4. Parse pipe segments and validate each command
    segments = command.split("|")
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        try:
            parts = shlex.split(segment)
        except ValueError:
            parts = segment.split()

        if not parts:
            continue

        base_cmd = parts[0]
        if base_cmd not in SAFE_COMMANDS:
            return f"Command `{base_cmd}` is not in the allowlist."

        # 5. Argument injection defense
        arg_err = _check_dangerous_args(base_cmd, parts)
        if arg_err:
            return arg_err

        # 6. Git subcommand validation
        if base_cmd == "git":
            if len(parts) < 2:
                return "git requires a subcommand."
            subcommand = parts[1]
            if subcommand not in ALLOWED_GIT_SUBCOMMANDS:
                return (
                    f"git subcommand `{subcommand}` is not allowed. "
                    f"Allowed: {', '.join(sorted(ALLOWED_GIT_SUBCOMMANDS))}"
                )

    return None


@authorized
async def shell_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text.strip()
    if not command:
        return

    user_id = update.effective_user.id

    # Handle keyboard button presses
    button_hints = {
        "Shell": "Type any allowlisted command (e.g. `ls`, `pwd`, `uptime`).",
        "Claude": "Use /claude <prompt> to ask Claude a question.",
        "Files": "Upload a document to save it to the working directory.",
        "Git": "Type a git command (e.g. `git status`, `git log`).",
        "Status": "Use /status to see system info.",
        "tmux": "Use /tmux ls or /tmux send <session> <cmd>.",
        "CD": "Use /cd to select a project directory on Desktop.",
        "Chat": "Use /chat to enter Claude chat mode for back-and-forth coding.",
        "New Project": "Use /newproject <name> to create a new project folder on Desktop.",
    }
    if command in button_hints:
        await update.message.reply_text(button_hints[command])
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

    error = validate_command(command)
    if error:
        logger.info("Blocked command from %s: %s — %s", user_id, command, error)
        log_action(user_id, "shell", command, result="blocked")
        await update.message.reply_text(f"Blocked: {error}")
        return

    logger.info("Running command from %s: %s", user_id, command)
    start_time = time.monotonic()
    output, return_code = await run_shell_command(command, cwd=get_working_dir(context))
    duration = time.monotonic() - start_time

    # Scrub secrets from output
    output = scrub_output(output)

    prefix = "" if return_code == 0 else f"[exit {return_code}]\n"
    full_output = prefix + output

    result = "ok" if return_code == 0 else f"exit_{return_code}"
    log_action(user_id, "shell", command, result=result, duration_s=duration)

    for chunk in chunk_text(full_output):
        await update.message.reply_text(f"```\n{chunk}\n```", parse_mode="Markdown")
