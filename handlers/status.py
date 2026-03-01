from telegram import Update
from telegram.ext import ContextTypes

from handlers.auth import authorized
from handlers.cd import get_working_dir
from utils.subprocess_runner import run_shell_command


@authorized
async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts: list[str] = []

    # Working directory
    parts.append(f"Working dir:\n{get_working_dir(context)}")

    # Uptime
    output, _ = await run_shell_command("uptime")
    parts.append(f"Uptime:\n{output}")

    # Disk
    output, _ = await run_shell_command("df -h /")
    parts.append(f"Disk:\n{output}")

    # Tailscale (optional — may not be installed yet)
    output, rc = await run_shell_command("tailscale status", timeout=5)
    if rc == 0:
        parts.append(f"Tailscale:\n{output}")
    else:
        parts.append("Tailscale: not running or not installed")

    await update.message.reply_text(
        f"```\n{chr(10).join(parts)}\n```",
        parse_mode="Markdown",
    )
