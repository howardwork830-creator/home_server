"""File browser and working-directory picker rooted at ~/Desktop.

/cd           — open interactive file browser
/cd <path>    — set working directory directly

Callback data scheme (all under ``br:`` prefix):
    br:N        tap item N (folder → navigate, file → action menu)
    br:back     parent directory
    br:pg:N     page N
    br:set      set browse_cwd as working dir
    br:dl:N     download file at index N
    br:info:N   show file info at index N
    br:fback    back from file-action menu to listing
    br:noop     page indicator (no-op)
"""

import datetime
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import AUTHORIZED_USER_IDS, MAX_UPLOAD_SIZE, WORK_DIR, logger
from handlers.auth import authorized
from utils.audit import log_action
from utils.path_guard import check_path

# ── Constants ────────────────────────────────────────────────────────────────

DESKTOP = Path.home() / "Desktop"
ITEMS_PER_PAGE = 8
MAX_LABEL_LEN = 40


# ── Public helper (imported by other handlers) ──────────────────────────────

def get_working_dir(context: ContextTypes.DEFAULT_TYPE) -> str:
    """Return the user's selected working directory, or the default WORK_DIR."""
    return context.user_data.get("working_dir", str(WORK_DIR))


# ── Internal helpers ─────────────────────────────────────────────────────────

def _resolve_safe_path(target: Path) -> Path | None:
    """Return *target* resolved, or None if it escapes ~/Desktop."""
    try:
        resolved = target.resolve()
    except (ValueError, OSError):
        return None
    if not str(resolved).startswith(str(DESKTOP.resolve())):
        return None
    return resolved


def _human_size(size: int) -> str:
    """Convert bytes to a human-readable string (B / KB / MB / GB)."""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            if unit == "B":
                return f"{size}{unit}"
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


def _scan_dir(directory: Path) -> list[dict]:
    """Return sorted listing: folders first, then files. Hidden files excluded."""
    items: list[dict] = []
    try:
        for entry in directory.iterdir():
            if entry.name.startswith("."):
                continue
            is_dir = entry.is_dir()
            try:
                size = 0 if is_dir else entry.stat().st_size
            except OSError:
                size = 0
            items.append({"name": entry.name, "is_dir": is_dir, "size": size})
    except PermissionError:
        pass
    # Folders first (alphabetically), then files (alphabetically)
    items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    return items


def _relative_display(directory: Path) -> str:
    """Return a display path like ``~/Desktop/foo/bar``."""
    try:
        rel = directory.resolve().relative_to(Path.home().resolve())
        return f"~/{rel}"
    except ValueError:
        return str(directory)


def _build_listing_keyboard(
    items: list[dict],
    page: int,
    browse_cwd: Path,
) -> InlineKeyboardMarkup:
    """Build the paged file/folder listing keyboard."""
    total_pages = max(1, (len(items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page = min(page, total_pages - 1)
    start = page * ITEMS_PER_PAGE
    page_items = items[start : start + ITEMS_PER_PAGE]

    buttons: list[list[InlineKeyboardButton]] = []

    for i, item in enumerate(page_items):
        idx = start + i
        if item["is_dir"]:
            label = f"\U0001f4c1 {item['name']}"
        else:
            sz = _human_size(item["size"])
            label = f"\U0001f4c4 {item['name']}  ({sz})"
        # Truncate long labels
        if len(label) > MAX_LABEL_LEN:
            label = label[: MAX_LABEL_LEN - 1] + "\u2026"
        buttons.append([InlineKeyboardButton(label, callback_data=f"br:{idx}")])

    # Pagination row
    if total_pages > 1:
        nav_row: list[InlineKeyboardButton] = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("\u25c0", callback_data=f"br:pg:{page - 1}"))
        nav_row.append(
            InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="br:noop")
        )
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("\u25b6", callback_data=f"br:pg:{page + 1}"))
        buttons.append(nav_row)

    # Bottom action row
    bottom: list[InlineKeyboardButton] = []
    bottom.append(InlineKeyboardButton("\u2713 Set as working dir", callback_data="br:set"))
    if browse_cwd.resolve() != DESKTOP.resolve():
        bottom.append(InlineKeyboardButton("\u2190 Back", callback_data="br:back"))
    buttons.append(bottom)

    return InlineKeyboardMarkup(buttons)


def _build_listing_text(browse_cwd: Path, items: list[dict]) -> str:
    """Header text for the file listing message."""
    display = _relative_display(browse_cwd)
    if not items:
        return f"\U0001f4c1 {display}\n\n(empty)"
    return f"\U0001f4c1 {display}"


def _build_file_action_keyboard(idx: int) -> InlineKeyboardMarkup:
    """Action menu for a tapped file."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\u2b07\ufe0f Download", callback_data=f"br:dl:{idx}")],
        [InlineKeyboardButton("\u2139\ufe0f Info", callback_data=f"br:info:{idx}")],
        [InlineKeyboardButton("\u2190 Back", callback_data="br:fback")],
    ])


def _store_browse_state(
    context: ContextTypes.DEFAULT_TYPE,
    cwd: Path,
    items: list[dict],
    page: int = 0,
) -> None:
    """Persist browse state in user_data."""
    context.user_data["browse_cwd"] = str(cwd)
    context.user_data["browse_items"] = items
    context.user_data["browse_page"] = page


# ── /cd command handler ─────────────────────────────────────────────────────

@authorized
async def cd_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cd — browse files or set working directory directly."""
    if context.args:
        # Direct path: /cd some/folder
        raw = " ".join(context.args)
        target = _resolve_safe_path(DESKTOP / raw)
        if target is None or not target.is_dir():
            await update.message.reply_text(
                "Invalid directory. Must be a folder under ~/Desktop."
            )
            return
        context.user_data["working_dir"] = str(target)
        await update.message.reply_text(
            f"Working dir set to:\n`{target}`", parse_mode="Markdown"
        )
        return

    # No args — start browsing from ~/Desktop
    items = _scan_dir(DESKTOP)
    _store_browse_state(context, DESKTOP, items, page=0)
    text = _build_listing_text(DESKTOP, items)
    kb = _build_listing_keyboard(items, 0, DESKTOP)
    await update.message.reply_text(text, reply_markup=kb)


# ── Callback query handler ──────────────────────────────────────────────────

async def cd_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all ``br:`` and legacy ``cd``/``cdset:`` callbacks."""
    query = update.callback_query
    await query.answer()

    # Auth check (callbacks bypass the @authorized decorator)
    if query.from_user.id not in AUTHORIZED_USER_IDS:
        await query.edit_message_text("Access denied.")
        return

    data = query.data

    # ── Legacy callbacks (cd: / cdset:) ──────────────────────────────────
    if data.startswith("cd:") or data.startswith("cdset:"):
        await query.edit_message_text("Please use /cd to browse again.")
        return

    # ── br:noop ──────────────────────────────────────────────────────────
    if data == "br:noop":
        return

    # ── Retrieve browse state ────────────────────────────────────────────
    browse_cwd_str = context.user_data.get("browse_cwd")
    browse_items = context.user_data.get("browse_items")
    browse_page = context.user_data.get("browse_page", 0)

    if browse_cwd_str is None or browse_items is None:
        await query.edit_message_text("Session expired. Please use /cd to browse again.")
        return

    browse_cwd = Path(browse_cwd_str)

    # ── br:set — set working directory ───────────────────────────────────
    if data == "br:set":
        resolved = _resolve_safe_path(browse_cwd)
        if resolved is None:
            await query.edit_message_text("Invalid directory.")
            return
        context.user_data["working_dir"] = str(resolved)
        display = _relative_display(resolved)
        logger.info("User %s set working_dir to %s", query.from_user.id, resolved)
        log_action(query.from_user.id, "cd", prompt=str(resolved), result="ok")
        await query.edit_message_text(f"Working dir set to:\n{display}")
        return

    # ── br:back — navigate to parent ─────────────────────────────────────
    if data == "br:back":
        parent = browse_cwd.parent
        safe = _resolve_safe_path(parent)
        if safe is None:
            # Already at Desktop boundary; stay put
            safe = DESKTOP
        items = _scan_dir(safe)
        _store_browse_state(context, safe, items, page=0)
        text = _build_listing_text(safe, items)
        kb = _build_listing_keyboard(items, 0, safe)
        await query.edit_message_text(text, reply_markup=kb)
        return

    # ── br:pg:N — pagination ─────────────────────────────────────────────
    if data.startswith("br:pg:"):
        try:
            page = int(data[len("br:pg:"):])
        except ValueError:
            return
        context.user_data["browse_page"] = page
        text = _build_listing_text(browse_cwd, browse_items)
        kb = _build_listing_keyboard(browse_items, page, browse_cwd)
        await query.edit_message_text(text, reply_markup=kb)
        return

    # ── br:fback — back from file action menu to listing ─────────────────
    if data == "br:fback":
        text = _build_listing_text(browse_cwd, browse_items)
        kb = _build_listing_keyboard(browse_items, browse_page, browse_cwd)
        await query.edit_message_text(text, reply_markup=kb)
        return

    # ── br:dl:N — download file ──────────────────────────────────────────
    if data.startswith("br:dl:"):
        try:
            idx = int(data[len("br:dl:"):])
        except ValueError:
            return
        if idx < 0 or idx >= len(browse_items):
            await query.edit_message_text("Item no longer available. Use /cd to refresh.")
            return
        item = browse_items[idx]
        if item["is_dir"]:
            await query.edit_message_text("Cannot download a directory.")
            return

        file_path = (browse_cwd / item["name"]).resolve()

        # Security check
        err = check_path(str(file_path))
        if err:
            log_action(query.from_user.id, "browse_download", prompt=str(file_path), result="blocked")
            await query.edit_message_text(f"Blocked: {err}")
            return

        if not file_path.is_file():
            await query.edit_message_text("File not found.")
            return

        size = file_path.stat().st_size
        if size > MAX_UPLOAD_SIZE:
            await query.edit_message_text(
                f"File too large ({_human_size(size)}). "
                f"Max is {MAX_UPLOAD_SIZE // (1024 * 1024)}MB."
            )
            return

        logger.info("Browse download by %s: %s (%d bytes)", query.from_user.id, file_path, size)
        log_action(query.from_user.id, "browse_download", prompt=str(file_path), result="ok")

        # Edit message to show we're sending, then send the document
        await query.edit_message_text(f"Sending {item['name']} ({_human_size(size)})\u2026")
        with open(file_path, "rb") as f:
            await query.message.reply_document(document=f, filename=item["name"])
        return

    # ── br:info:N — file info ────────────────────────────────────────────
    if data.startswith("br:info:"):
        try:
            idx = int(data[len("br:info:"):])
        except ValueError:
            return
        if idx < 0 or idx >= len(browse_items):
            await query.edit_message_text("Item no longer available. Use /cd to refresh.")
            return
        item = browse_items[idx]
        file_path = (browse_cwd / item["name"]).resolve()

        try:
            stat = file_path.stat()
        except OSError:
            await query.edit_message_text("Cannot read file info.")
            return

        ext = file_path.suffix or "(none)"
        modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        info_text = (
            f"Name: {item['name']}\n"
            f"Size: {_human_size(stat.st_size)}\n"
            f"Modified: {modified}\n"
            f"Extension: {ext}\n"
            f"Path: {file_path}"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("\u2b07\ufe0f Download", callback_data=f"br:dl:{idx}")],
            [InlineKeyboardButton("\u2190 Back", callback_data="br:fback")],
        ])
        await query.edit_message_text(info_text, reply_markup=kb)
        return

    # ── br:N — tap item (folder → navigate, file → action menu) ─────────
    if data.startswith("br:"):
        try:
            idx = int(data[len("br:"):])
        except ValueError:
            return
        if idx < 0 or idx >= len(browse_items):
            await query.edit_message_text("Item no longer available. Use /cd to refresh.")
            return
        item = browse_items[idx]

        if item["is_dir"]:
            # Navigate into folder
            target = _resolve_safe_path(browse_cwd / item["name"])
            if target is None:
                await query.edit_message_text("Cannot open this directory.")
                return
            items = _scan_dir(target)
            _store_browse_state(context, target, items, page=0)
            text = _build_listing_text(target, items)
            kb = _build_listing_keyboard(items, 0, target)
            await query.edit_message_text(text, reply_markup=kb)
        else:
            # Show file action menu
            sz = _human_size(item["size"])
            text = f"\U0001f4c4 {item['name']}  ({sz})"
            kb = _build_file_action_keyboard(idx)
            await query.edit_message_text(text, reply_markup=kb)
        return
