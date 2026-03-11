import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import APP_LAUNCH_ALLOWLIST, AUTHORIZED_USER_IDS, logger
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

    # /app — show interactive app menu
    if not args:
        output, rc = await run_shell_command(
            "osascript -e 'tell application \"System Events\" to get name of "
            "every process whose background only is false'",
            timeout=10,
        )
        running = []
        if rc == 0:
            running = [a.strip() for a in output.split(",") if a.strip()]

        buttons = []
        # Running apps — tap to quit
        if running:
            buttons.append([InlineKeyboardButton(
                f"--- Running ({len(running)}) ---", callback_data="app:noop"
            )])
            for a in sorted(running):
                cb = f"app:quit:{a}"
                if len(cb.encode("utf-8")) <= 64:
                    buttons.append([InlineKeyboardButton(
                        f"⏹ {a}", callback_data=cb
                    )])

        # Launchable apps
        not_running = sorted(APP_LAUNCH_ALLOWLIST - set(running))
        if not_running:
            buttons.append([InlineKeyboardButton(
                "--- Launch ---", callback_data="app:noop"
            )])
            for a in not_running:
                cb = f"app:launch:{a}"
                if len(cb.encode("utf-8")) <= 64:
                    buttons.append([InlineKeyboardButton(
                        f"▶️ {a}", callback_data=cb
                    )])

        if not buttons:
            await update.message.reply_text("No apps found and none in launch allowlist.")
            return
        await update.message.reply_text(
            "Applications", reply_markup=InlineKeyboardMarkup(buttons)
        )
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


async def app_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button taps for /app."""
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in AUTHORIZED_USER_IDS:
        await query.edit_message_text("Access denied.")
        return

    data = query.data

    if data == "app:noop":
        return

    if data.startswith("app:launch:"):
        name = data[len("app:launch:"):]
        if name not in APP_LAUNCH_ALLOWLIST:
            await query.edit_message_text(f"App '{name}' not in launch allowlist.")
            return
        output, rc = await run_shell_command(f"open -a '{name}'", timeout=10)
        await query.edit_message_text(
            f"Launched {name}." if rc == 0 else f"Failed to launch {name}:\n{output}"
        )
        logger.info("App callback by %s: launch %s", query.from_user.id, name)
        return

    if data.startswith("app:quit:"):
        name = data[len("app:quit:"):]
        output, rc = await run_shell_command(
            f"osascript -e 'tell application \"{name}\" to quit'", timeout=10
        )
        await query.edit_message_text(
            f"Sent quit to {name}." if rc == 0 else f"Failed to quit {name}:\n{output}"
        )
        logger.info("App callback by %s: quit %s", query.from_user.id, name)
        return
