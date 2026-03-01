from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import AUTHORIZED_USER_IDS, WORK_DIR, logger
from handlers.auth import authorized

DESKTOP = Path.home() / "Desktop"


def get_working_dir(context: ContextTypes.DEFAULT_TYPE) -> str:
    """Return the user's selected working directory, or the default WORK_DIR."""
    return context.user_data.get("working_dir", str(WORK_DIR))


def _resolve_safe_path(relative: str) -> Path | None:
    """Resolve *relative* under ~/Desktop and reject anything outside it."""
    try:
        target = (DESKTOP / relative).resolve()
    except (ValueError, OSError):
        return None
    # Must be inside Desktop and be a directory
    if not str(target).startswith(str(DESKTOP.resolve())):
        return None
    if not target.is_dir():
        return None
    return target


def _dir_keyboard(parent: Path, prefix: str = "cd") -> InlineKeyboardMarkup:
    """Build an inline keyboard listing subdirectories of *parent*."""
    dirs = sorted(
        [d for d in parent.iterdir() if d.is_dir() and not d.name.startswith(".")],
        key=lambda d: d.name.lower(),
    )
    buttons = [
        [InlineKeyboardButton(d.name, callback_data=f"{prefix}:{d.name}")]
        for d in dirs
    ]
    return InlineKeyboardMarkup(buttons)


@authorized
async def cd_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cd — list Desktop directories or set one directly."""
    if context.args:
        # Direct path: /cd VS code file/home server
        raw = " ".join(context.args)
        target = _resolve_safe_path(raw)
        if target is None:
            await update.message.reply_text(
                "Invalid directory. Must be a folder under ~/Desktop."
            )
            return
        context.user_data["working_dir"] = str(target)
        await update.message.reply_text(f"Working dir set to:\n`{target}`", parse_mode="Markdown")
        return

    # No args — show top-level Desktop directories
    kb = _dir_keyboard(DESKTOP)
    if not kb.inline_keyboard:
        await update.message.reply_text("No directories found on Desktop.")
        return
    await update.message.reply_text("Select a project directory:", reply_markup=kb)


async def cd_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button taps for directory selection."""
    query = update.callback_query
    await query.answer()

    # Auth check (callbacks bypass the @authorized decorator)
    if query.from_user.id not in AUTHORIZED_USER_IDS:
        await query.edit_message_text("Access denied.")
        return

    data = query.data  # e.g. "cd:VS code file" or "cdset:VS code file/home server"

    # --- "Back" button → re-show top-level listing ---
    if data == "cd:__back__":
        kb = _dir_keyboard(DESKTOP)
        await query.edit_message_text("Select a project directory:", reply_markup=kb)
        return

    # --- "cdset:<path>" → user confirmed selection ---
    if data.startswith("cdset:"):
        rel = data[len("cdset:"):]
        target = _resolve_safe_path(rel)
        if target is None:
            await query.edit_message_text("Invalid directory.")
            return
        context.user_data["working_dir"] = str(target)
        await query.edit_message_text(
            f"Working dir set to:\n{target}"
        )
        logger.info("User %s set working_dir to %s", query.from_user.id, target)
        return

    # --- "cd:<dirname>" → tapped a directory ---
    if data.startswith("cd:"):
        name = data[len("cd:"):]
        target = _resolve_safe_path(name)
        if target is None:
            await query.edit_message_text("Invalid directory.")
            return

        # Check for subdirectories
        subdirs = sorted(
            [d for d in target.iterdir() if d.is_dir() and not d.name.startswith(".")],
            key=lambda d: d.name.lower(),
        )

        buttons = [
            [InlineKeyboardButton(
                f"\u2713 Select: {name}/",
                callback_data=f"cdset:{name}",
            )]
        ]
        for sd in subdirs:
            rel = f"{name}/{sd.name}"
            buttons.append(
                [InlineKeyboardButton(sd.name, callback_data=f"cdset:{rel}")]
            )
        buttons.append(
            [InlineKeyboardButton("\u2190 Back", callback_data="cd:__back__")]
        )

        await query.edit_message_text(
            f"Contents of {name}/:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return
