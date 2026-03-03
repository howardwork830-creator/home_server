import re

from telegram import Update
from telegram.ext import ContextTypes

from config import APP_LAUNCH_ALLOWLIST, logger
from handlers.auth import authorized
from utils.subprocess_runner import run_shell_command

_UNSAFE_NAME = re.compile(r'["/`$\\;|&<>(){}]|\.\.')


def _sanitize_app_name(name: str) -> str | None:
    """Validate and sanitize an app name. Returns None if unsafe."""
    name = name.strip().strip("'")
    if not name or _UNSAFE_NAME.search(name):
        return None
    return name


@authorized
async def app_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /app — list, launch, quit, or kill macOS GUI applications."""
    args = context.args or []

    # /app — list running GUI apps
    if not args:
        output, rc = await run_shell_command(
            "osascript -e 'tell application \"System Events\" to get name of "
            "every process whose background only is false'",
            timeout=10,
        )
        if rc != 0:
            await update.message.reply_text(f"Failed to list apps:\n```\n{output}\n```", parse_mode="Markdown")
            return
        # osascript returns comma-separated names
        apps = [a.strip() for a in output.split(",") if a.strip()]
        if not apps:
            await update.message.reply_text("No running GUI applications found.")
            return
        listing = "\n".join(f"  - {a}" for a in sorted(apps))
        await update.message.reply_text(f"Running apps ({len(apps)}):\n{listing}")
        return

    action = args[0].lower()
    name_parts = args[1:]

    if action not in ("launch", "quit", "kill"):
        await update.message.reply_text(
            "Usage:\n"
            "/app — list running apps\n"
            "/app launch <name>\n"
            "/app quit <name>\n"
            "/app kill <name>"
        )
        return

    if not name_parts:
        await update.message.reply_text(f"Usage: /app {action} <app name>")
        return

    raw_name = " ".join(name_parts)
    name = _sanitize_app_name(raw_name)
    if name is None:
        await update.message.reply_text("Invalid app name (contains unsafe characters).")
        return

    if action == "launch":
        if name not in APP_LAUNCH_ALLOWLIST:
            allowed = ", ".join(sorted(APP_LAUNCH_ALLOWLIST))
            await update.message.reply_text(
                f"App '{name}' is not in the launch allowlist.\n\nAllowed: {allowed}"
            )
            return
        output, rc = await run_shell_command(f"open -a '{name}'", timeout=10)
        if rc == 0:
            await update.message.reply_text(f"Launched {name}.")
        else:
            await update.message.reply_text(f"Failed to launch {name}:\n```\n{output}\n```", parse_mode="Markdown")

    elif action == "quit":
        output, rc = await run_shell_command(
            f"osascript -e 'tell application \"{name}\" to quit'", timeout=10
        )
        if rc == 0:
            await update.message.reply_text(f"Sent quit to {name}.")
        else:
            await update.message.reply_text(f"Failed to quit {name}:\n```\n{output}\n```", parse_mode="Markdown")

    elif action == "kill":
        output, rc = await run_shell_command(f"killall '{name}'", timeout=10)
        if rc == 0:
            await update.message.reply_text(f"Force-killed {name}.")
        else:
            await update.message.reply_text(f"Failed to kill {name}:\n```\n{output}\n```", parse_mode="Markdown")

    logger.info("App action by %s: %s %s", update.effective_user.id, action, name)
