"""Handler for /tools — quick-action button grid for common shell tasks.

Replaces the need to type CLI commands by offering pre-built buttons
that execute frequently used commands and return the output.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import AUTHORIZED_USER_IDS, logger
from handlers.auth import authorized
from handlers.cd import get_working_dir
from utils.chunker import chunk_text
from utils.scrubber import scrub_output
from utils.subprocess_runner import run_shell_command

# ── Quick actions: (label, callback_key, command_template) ──────────────
# Commands can use {cwd} placeholder for the user's working directory.

TOOL_CATEGORIES = [
    ("Files", [
        ("ls -la",       "tl:ls",      "ls -la {cwd}"),
        ("tree",         "tl:tree",    "tree -L 2 {cwd}"),
        ("du (sizes)",   "tl:du",      "du -sh {cwd}/*"),
        ("find recent",  "tl:recent",  "find {cwd} -maxdepth 2 -type f -mtime -7 | head -30"),
    ]),
    ("System", [
        ("ps (top 15)",  "tl:ps",      "ps aux | head -16"),
        ("df (disk)",    "tl:df",      "df -h"),
        ("uptime",       "tl:uptime",  "uptime"),
        ("top (snap)",   "tl:top",     "top -l 1 -n 10 | head -22"),
    ]),
    ("Network", [
        ("ping 1.1.1.1", "tl:ping",    "ping -c 3 1.1.1.1"),
        ("ifconfig",     "tl:ifconf",  "ifconfig | grep -A 2 'inet '"),
        ("tailscale",    "tl:ts",      "tailscale status"),
        ("netstat",      "tl:net",     "netstat -an | grep LISTEN | head -15"),
    ]),
    ("Dev", [
        ("git status",   "tl:git",     "cd {cwd} && git status"),
        ("git log",      "tl:gitlog",  "cd {cwd} && git log --oneline -10"),
        ("brew outdated", "tl:brew",   "brew outdated"),
        ("python3 -V",   "tl:pyver",   "python3 --version"),
    ]),
]

# Build a flat lookup: callback_data -> command_template
_TOOL_COMMANDS = {}
for _cat_name, _tools in TOOL_CATEGORIES:
    for _label, _cb, _cmd in _tools:
        _TOOL_COMMANDS[_cb] = _cmd


@authorized
async def tools_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tools — show quick-action button grid."""
    buttons = []
    for cat_name, tools in TOOL_CATEGORIES:
        buttons.append([InlineKeyboardButton(
            f"--- {cat_name} ---", callback_data="tl:noop"
        )])
        row = []
        for label, cb, _cmd in tools:
            row.append(InlineKeyboardButton(label, callback_data=cb))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
    await update.message.reply_text(
        "Quick Tools (tap to run):",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def tools_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button taps for /tools."""
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in AUTHORIZED_USER_IDS:
        await query.edit_message_text("Access denied.")
        return

    data = query.data

    if data == "tl:noop":
        return

    cmd_template = _TOOL_COMMANDS.get(data)
    if cmd_template is None:
        await query.edit_message_text("Unknown tool action.")
        return

    cwd = get_working_dir(context)
    cmd = cmd_template.replace("{cwd}", cwd)

    await query.edit_message_text(f"Running: `{cmd}`...", parse_mode="Markdown")
    logger.info("Tool action by %s: %s", query.from_user.id, cmd)

    output, rc = await run_shell_command(cmd, timeout=30)
    output = scrub_output(output)

    prefix = "" if rc == 0 else f"[exit {rc}]\n"
    full_output = prefix + (output or "(no output)")

    chunks = chunk_text(full_output)
    # Edit the first chunk into the existing message
    await query.edit_message_text(f"```\n{chunks[0]}\n```", parse_mode="Markdown")
    # Send any remaining chunks as new messages
    for chunk in chunks[1:]:
        await query.message.reply_text(f"```\n{chunk}\n```", parse_mode="Markdown")
