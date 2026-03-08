import os
import re

from telegram import Update
from telegram.ext import ContextTypes

from config import STEAM_GAMES, STEAM_APP_PATH, logger
from handlers.auth import authorized
from utils.subprocess_runner import run_shell_command

_UNSAFE_NAME = re.compile(r'["/`$\\;|&<>(){}]|\.\.')

TIPS_TEXT = """Steam Remote Play Tips:

1. Install the Steam Link app on your phone
2. Sign into the same Steam account on both devices
3. On the Mac, Steam must be in Big Picture mode for Remote Play
   Use: /steam bigpicture

4. Tailscale + Steam Link workaround:
   Steam Link may fail to find your Mac when Tailscale is active.
   Fix: In Steam Link settings, disable "Use Tailscale subnets"
   (or connect via the Mac's Tailscale IP manually)

5. Alternative: Moonlight + Sunshine
   For lower latency game streaming, install Sunshine on the Mac
   and Moonlight on your phone. Works great over Tailscale."""

HELP_TEXT = """Steam Remote Play commands:

/steam status — Check if Steam is running
/steam start — Launch Steam
/steam quit — Quit Steam cleanly
/steam bigpicture — Enter Big Picture mode (auto-starts Steam)
/steam play <name> — Launch a game from your allowlist
/steam games — List configured games
/steam tips — Setup tips (Steam Link, Tailscale workaround)"""


def _sanitize_game_name(name: str) -> str | None:
    """Validate and sanitize a game name. Returns None if unsafe."""
    name = name.strip()
    if not name or _UNSAFE_NAME.search(name):
        return None
    return name


def _find_game(query: str) -> tuple[str, int] | None:
    """Find a game by name (case-insensitive exact, then unique substring).

    Returns (canonical_name, app_id) or None.
    """
    if not STEAM_GAMES:
        return None

    lower_query = query.lower()

    # Exact match (case-insensitive)
    for name, app_id in STEAM_GAMES.items():
        if name.lower() == lower_query:
            return (name, app_id)

    # Unique substring match
    matches = [
        (name, app_id)
        for name, app_id in STEAM_GAMES.items()
        if lower_query in name.lower()
    ]
    if len(matches) == 1:
        return matches[0]

    return None


@authorized
async def steam_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /steam — control Steam and Remote Play."""
    args = context.args or []

    if not args or args[0].lower() == "help":
        await update.message.reply_text(HELP_TEXT)
        return

    action = args[0].lower()

    if action == "status":
        output, rc = await run_shell_command("pgrep -x Steam", timeout=10)
        if rc == 0:
            await update.message.reply_text("Steam is running.")
        else:
            await update.message.reply_text("Steam is not running.")

    elif action == "start":
        if not os.path.isdir(STEAM_APP_PATH):
            await update.message.reply_text(
                f"Steam not found at {STEAM_APP_PATH}. Install Steam first."
            )
            return
        output, rc = await run_shell_command(f"open -a Steam", timeout=10)
        if rc == 0:
            await update.message.reply_text("Steam launched.")
        else:
            await update.message.reply_text(
                f"Failed to launch Steam:\n```\n{output}\n```",
                parse_mode="Markdown",
            )

    elif action == "quit":
        output, rc = await run_shell_command("open steam://exit", timeout=10)
        if rc == 0:
            await update.message.reply_text("Sent quit signal to Steam.")
        else:
            await update.message.reply_text(
                f"Failed to quit Steam:\n```\n{output}\n```",
                parse_mode="Markdown",
            )

    elif action == "bigpicture":
        # Auto-start Steam if not running
        check_output, check_rc = await run_shell_command("pgrep -x Steam", timeout=10)
        if check_rc != 0:
            if not os.path.isdir(STEAM_APP_PATH):
                await update.message.reply_text(
                    f"Steam not found at {STEAM_APP_PATH}. Install Steam first."
                )
                return
            await run_shell_command("open -a Steam", timeout=10)
            await update.message.reply_text("Starting Steam...")

        output, rc = await run_shell_command(
            "open steam://open/bigpicture", timeout=10
        )
        if rc == 0:
            await update.message.reply_text("Big Picture mode activated.")
        else:
            await update.message.reply_text(
                f"Failed to open Big Picture:\n```\n{output}\n```",
                parse_mode="Markdown",
            )

    elif action == "play":
        if len(args) < 2:
            await update.message.reply_text("Usage: /steam play <game name>")
            return

        raw_name = " ".join(args[1:])
        name = _sanitize_game_name(raw_name)
        if name is None:
            await update.message.reply_text(
                "Invalid game name (contains unsafe characters)."
            )
            return

        result = _find_game(name)
        if result is None:
            if not STEAM_GAMES:
                await update.message.reply_text(
                    "No games configured. Edit STEAM_GAMES in config/steam.py."
                )
            else:
                games_list = "\n".join(f"  - {g}" for g in sorted(STEAM_GAMES))
                await update.message.reply_text(
                    f"Game '{name}' not found.\n\nAvailable games:\n{games_list}"
                )
            return

        canonical_name, app_id = result
        output, rc = await run_shell_command(
            f"open steam://rungameid/{app_id}", timeout=10
        )
        if rc == 0:
            await update.message.reply_text(f"Launching {canonical_name}...")
        else:
            await update.message.reply_text(
                f"Failed to launch {canonical_name}:\n```\n{output}\n```",
                parse_mode="Markdown",
            )

    elif action == "games":
        if not STEAM_GAMES:
            await update.message.reply_text(
                "No games configured.\n\n"
                "Add games to STEAM_GAMES in config/steam.py:\n"
                '  "Counter-Strike 2": 730,\n'
                '  "Stardew Valley": 413150,'
            )
            return
        listing = "\n".join(
            f"  - {name} (ID: {app_id})" for name, app_id in sorted(STEAM_GAMES.items())
        )
        await update.message.reply_text(
            f"Configured games ({len(STEAM_GAMES)}):\n{listing}"
        )

    elif action == "tips":
        await update.message.reply_text(TIPS_TEXT)

    else:
        await update.message.reply_text(HELP_TEXT)
        return

    logger.info("Steam action by %s: %s", update.effective_user.id, " ".join(args))
