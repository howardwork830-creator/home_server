"""Handler for /t — manage persistent terminal sessions."""

from telegram import Update
from telegram.ext import ContextTypes

from config import MAX_TERMINALS, logger
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

    # /t or /t list — list terminals
    if not args or args[0] == "list":
        if not terminals:
            await update.message.reply_text("No active terminals. Send a command to auto-create one.")
            return
        active = _get_active(context)
        lines = []
        for slot in sorted(terminals):
            info = terminals[slot]
            marker = " *" if slot == active else ""
            lines.append(f"  {slot}: {info['name']}{marker}")
        await update.message.reply_text(
            "Terminals (* = active):\n" + "\n".join(lines)
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
