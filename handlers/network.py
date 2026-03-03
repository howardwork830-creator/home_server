from telegram import Update
from telegram.ext import ContextTypes

from config import TAILSCALE_STATUS_TIMEOUT
from handlers.auth import authorized
from utils.subprocess_runner import run_shell_command


@authorized
async def network_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts: list[str] = []

    # Local interfaces
    output, rc = await run_shell_command(
        "ifconfig | grep -E '^[a-z]|inet '", timeout=5
    )
    if rc == 0:
        parts.append(f"Interfaces:\n{output}")
    else:
        parts.append("Interfaces: unavailable")

    # Public IP
    output, rc = await run_shell_command(
        "curl -s --max-time 5 ifconfig.me", timeout=10
    )
    if rc == 0 and output.strip():
        parts.append(f"Public IP: {output.strip()}")
    else:
        parts.append("Public IP: unavailable")

    # Connectivity check
    output, rc = await run_shell_command("ping -c 1 -W 3 8.8.8.8", timeout=10)
    if rc == 0:
        parts.append("Connectivity: OK (8.8.8.8 reachable)")
    else:
        parts.append("Connectivity: FAILED (8.8.8.8 unreachable)")

    # Tailscale VPN
    output, rc = await run_shell_command(
        "tailscale status", timeout=TAILSCALE_STATUS_TIMEOUT
    )
    if rc == 0:
        parts.append(f"Tailscale:\n{output}")
    else:
        parts.append("Tailscale: not running or not installed")

    body = "\n".join(parts)
    await update.message.reply_text(
        f"```\n{body}\n```",
        parse_mode="Markdown",
    )
