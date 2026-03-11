"""Handler for /t — manage persistent terminal sessions."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import AUTHORIZED_USER_IDS, MAX_TERMINALS, logger
from handlers.auth import authorized
from handlers.cd import get_working_dir
from utils.terminal_manager import create_session, kill_session, session_exists


def _get_terminals(context: ContextTypes.DEFAULT_TYPE) -> dict:
    """Get the user's terminals dict, initializing if needed."""
    if "terminals" not in context.user_data:
        context.user_data["terminals"] = {}
    return context.user_data["terminals"]


def _get_active(context: ContextTypes.DEFAULT_TYPE) -> int | None:
    return context.user_data.get("active_terminal")


def _set_active(context: ContextTypes.DEFAULT_TYPE, slot: int | None):
    context.user_data["active_terminal"] = slot


def _next_slot(terminals: dict) -> int | None:
    """Find the lowest available slot (1-based) up to MAX_TERMINALS."""
    for i in range(1, MAX_TERMINALS + 1):
        if i not in terminals:
            return i
    return None


async def ensure_terminal(
    user_id: int, context: ContextTypes.DEFAULT_TYPE
) -> tuple[int, str]:
    """Ensure the user has an active terminal. Auto-creates one if needed.

    Returns (slot, tmux_session_name).
    """
    terminals = _get_terminals(context)
    active = _get_active(context)

    if active and active in terminals:
        return active, terminals[active]["tmux_session"]

    # Auto-create terminal 1
    slot = _next_slot(terminals)
    if slot is None:
        raise RuntimeError("Maximum terminals reached.")

    cwd = get_working_dir(context)
    tmux_name = await create_session(user_id, slot, cwd)
    terminals[slot] = {"name": f"T{slot}", "tmux_session": tmux_name}
    _set_active(context, slot)
    logger.info("Auto-created terminal %d for user %s", slot, user_id)
    return slot, tmux_name


async def close_terminal(
    user_id: int, slot: int, context: ContextTypes.DEFAULT_TYPE
) -> str | None:
    """Close a terminal by slot. Returns error message or None on success."""
    terminals = _get_terminals(context)
    if slot not in terminals:
        return f"Terminal {slot} does not exist."

    info = terminals.pop(slot)
    await kill_session(info["tmux_session"])

    # Adjust active terminal
    if _get_active(context) == slot:
        remaining = sorted(terminals.keys())
        _set_active(context, remaining[0] if remaining else None)

    logger.info("User %s closed terminal %d", user_id, slot)
    return None


@authorized
async def terminal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /t command for terminal management."""
    user_id = update.effective_user.id
    args = context.args or []
    terminals = _get_terminals(context)

    # /t or /t list — show interactive terminal menu
    if not args or args[0] == "list":
        if not terminals:
            buttons = [
                [InlineKeyboardButton("➕ New Terminal", callback_data="term:new")],
            ]
            await update.message.reply_text(
                "No active terminals.",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
            return
        active = _get_active(context)
        buttons = []
        for slot in sorted(terminals):
            info = terminals[slot]
            marker = " ✓" if slot == active else ""
            buttons.append([
                InlineKeyboardButton(
                    f"T{slot}: {info['name']}{marker}",
                    callback_data=f"term:sw:{slot}",
                ),
                InlineKeyboardButton(
                    "❌", callback_data=f"term:close:{slot}",
                ),
            ])
        # Add "New" button if under limit
        if len(terminals) < MAX_TERMINALS:
            buttons.append([InlineKeyboardButton(
                "➕ New Terminal", callback_data="term:new"
            )])
        await update.message.reply_text(
            "Terminals (tap to switch, ❌ to close):",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    # /t new [name] — create a new terminal
    if args[0] == "new":
        slot = _next_slot(terminals)
        if slot is None:
            await update.message.reply_text(f"Maximum of {MAX_TERMINALS} terminals reached.")
            return
        name = " ".join(args[1:]) if len(args) > 1 else f"T{slot}"
        cwd = get_working_dir(context)
        tmux_name = await create_session(user_id, slot, cwd)
        terminals[slot] = {"name": name, "tmux_session": tmux_name}
        _set_active(context, slot)
        await update.message.reply_text(
            f"Created terminal {slot} ({name}). Use `/t {slot}` to switch."
        )
        return

    # /t close <id> — close a terminal
    if args[0] == "close":
        if len(args) < 2:
            await update.message.reply_text("Usage: `/t close <id>`")
            return
        try:
            slot = int(args[1])
        except ValueError:
            await update.message.reply_text("Terminal ID must be a number.")
            return
        err = await close_terminal(user_id, slot, context)
        if err:
            await update.message.reply_text(err)
            return
        active = _get_active(context)
        fallback = f" Active terminal: {active}" if active else " No active terminals."
        await update.message.reply_text(f"Closed terminal {slot}.{fallback}")
        return

    # /t <id> or /t use <id> — switch active terminal
    raw = args[1] if args[0] == "use" and len(args) > 1 else args[0]
    try:
        slot = int(raw)
    except ValueError:
        await update.message.reply_text(
            "Usage: `/t`, `/t new [name]`, `/t <id>`, `/t close <id>`"
        )
        return

    if slot not in terminals:
        await update.message.reply_text(f"Terminal {slot} does not exist.")
        return

    # Verify tmux session still alive
    if not await session_exists(terminals[slot]["tmux_session"]):
        terminals.pop(slot)
        remaining = sorted(terminals.keys())
        _set_active(context, remaining[0] if remaining else None)
        await update.message.reply_text(f"Terminal {slot} session expired and was removed.")
        return

    _set_active(context, slot)
    name = terminals[slot]["name"]
    await update.message.reply_text(f"Switched to terminal {slot} ({name}).")


async def terminal_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button taps for /t."""
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in AUTHORIZED_USER_IDS:
        await query.edit_message_text("Access denied.")
        return

    user_id = query.from_user.id
    data = query.data
    terminals = _get_terminals(context)

    if data == "term:new":
        slot = _next_slot(terminals)
        if slot is None:
            await query.edit_message_text(f"Maximum of {MAX_TERMINALS} terminals reached.")
            return
        cwd = get_working_dir(context)
        tmux_name = await create_session(user_id, slot, cwd)
        terminals[slot] = {"name": f"T{slot}", "tmux_session": tmux_name}
        _set_active(context, slot)
        await query.edit_message_text(f"Created terminal {slot}. Now active.")
        return

    if data.startswith("term:sw:"):
        try:
            slot = int(data[len("term:sw:"):])
        except ValueError:
            return
        if slot not in terminals:
            await query.edit_message_text(f"Terminal {slot} does not exist.")
            return
        if not await session_exists(terminals[slot]["tmux_session"]):
            terminals.pop(slot)
            remaining = sorted(terminals.keys())
            _set_active(context, remaining[0] if remaining else None)
            await query.edit_message_text(f"Terminal {slot} expired and was removed.")
            return
        _set_active(context, slot)
        name = terminals[slot]["name"]
        await query.edit_message_text(f"Switched to terminal {slot} ({name}).")
        return

    if data.startswith("term:close:"):
        try:
            slot = int(data[len("term:close:"):])
        except ValueError:
            return
        err = await close_terminal(user_id, slot, context)
        if err:
            await query.edit_message_text(err)
            return
        active = _get_active(context)
        fallback = f" Active: {active}" if active else " No active terminals."
        await query.edit_message_text(f"Closed terminal {slot}.{fallback}")
