import asyncio
import os
import tempfile

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import ContextTypes

from config import AUTHORIZED_USER_IDS, GO2RTC_HOST, MINIAPP_BASE_URL, logger
from handlers.auth import authorized


async def _capture_screenshot():
    """Capture screen to a temp JPEG and resize for Telegram."""
    path = os.path.join(tempfile.gettempdir(), "monitor_screen.jpg")
    proc = await asyncio.create_subprocess_exec(
        "screencapture", "-x", "-t", "jpg", path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await asyncio.wait_for(proc.wait(), timeout=10)
    if proc.returncode != 0 or not os.path.exists(path):
        return None

    # Resize to 1920px wide for faster transfer
    proc = await asyncio.create_subprocess_exec(
        "sips", "--resampleWidth", "1920", path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await asyncio.wait_for(proc.wait(), timeout=10)

    if os.path.getsize(path) == 0:
        return None
    return path


def _build_keyboard():
    """Build inline keyboard with Refresh and optional Live Monitor button."""
    buttons = [InlineKeyboardButton("Refresh", callback_data="monitor_refresh")]
    rows = [buttons]
    if GO2RTC_HOST and MINIAPP_BASE_URL:
        url = f"{MINIAPP_BASE_URL}/monitor.html?server={GO2RTC_HOST}"
        rows.append([InlineKeyboardButton(
            "Open Live Monitor", web_app=WebAppInfo(url=url),
        )])
    return InlineKeyboardMarkup(rows)


@authorized
async def monitor_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture a screenshot and send it as a photo."""
    msg = await update.message.reply_text("Capturing screen...")
    path = await _capture_screenshot()
    if not path:
        await msg.edit_text("Failed to capture screen.")
        return
    try:
        with open(path, "rb") as f:
            await update.message.reply_photo(photo=f, reply_markup=_build_keyboard())
        await msg.delete()
    finally:
        os.remove(path)


async def monitor_refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Refresh button — capture and send a new screenshot."""
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in AUTHORIZED_USER_IDS:
        return

    path = await _capture_screenshot()
    if not path:
        await query.message.reply_text("Failed to capture screen.")
        return
    try:
        with open(path, "rb") as f:
            await query.message.reply_photo(photo=f, reply_markup=_build_keyboard())
    finally:
        os.remove(path)
