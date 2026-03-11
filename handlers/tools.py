"""Handler for /tools — category-based tool hub for remote coding.

Main menu shows 8 categories in a 2-column grid. Tapping a category
shows its tools + a Back button. Tapping a tool runs it, shows a link
hint, or displays info text.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import AUTHORIZED_USER_IDS, logger
from handlers.auth import authorized
from handlers.cd import get_working_dir
from utils.chunker import chunk_text
from utils.scrubber import scrub_output
from utils.subprocess_runner import run_shell_command

# ── Categories (main menu order) ─────────────────────────────────────

CATEGORIES = [
    {"id": "files",  "label": "Files",     "icon": "\U0001f4c2"},
    {"id": "git",    "label": "Git",       "icon": "\U0001f500"},
    {"id": "dev",    "label": "Code/Dev",  "icon": "\U0001f6e0\ufe0f"},
    {"id": "term",   "label": "Terminals", "icon": "\U0001f4bb"},
    {"id": "claude", "label": "Claude AI", "icon": "\U0001f916"},
    {"id": "system", "label": "System",    "icon": "\U0001f4ca"},
    {"id": "net",    "label": "Network",   "icon": "\U0001f310"},
    {"id": "apps",   "label": "Apps",      "icon": "\U0001f4f1"},
]

# ── Tools per category ───────────────────────────────────────────────
# type: "cmd"  — runs a shell command template ({cwd} is replaced)
# type: "link" — shows "Use /command" message with Back button
# type: "info" — shows static text with Back button

CATEGORY_TOOLS = {
    "files": [
        {"label": "ls -la",      "id": "ls",       "type": "cmd", "cmd": "ls -la {cwd}"},
        {"label": "tree",        "id": "tree",     "type": "cmd", "cmd": "tree -L 2 {cwd}"},
        {"label": "du (sizes)",  "id": "du",       "type": "cmd", "cmd": "du -sh {cwd}/*"},
        {"label": "find recent", "id": "recent",   "type": "cmd", "cmd": "find {cwd} -maxdepth 2 -type f -mtime -7 | head -30"},
        {"label": "wc (lines)",  "id": "wc",       "type": "cmd", "cmd": "find {cwd} -maxdepth 1 -type f | head -20 | xargs wc -l"},
        {"label": "file types",  "id": "ftypes",   "type": "cmd", "cmd": "find {cwd} -maxdepth 2 -type f | sed 's/.*\\.//' | sort | uniq -c | sort -rn | head -15"},
    ],
    "git": [
        {"label": "status",      "id": "gst",      "type": "cmd", "cmd": "cd {cwd} && git status"},
        {"label": "log (10)",    "id": "glog",     "type": "cmd", "cmd": "cd {cwd} && git log --oneline -10"},
        {"label": "diff",        "id": "gdiff",    "type": "cmd", "cmd": "cd {cwd} && git diff"},
        {"label": "diff --stat", "id": "gdstat",   "type": "cmd", "cmd": "cd {cwd} && git diff --stat"},
        {"label": "branch",      "id": "gbranch",  "type": "cmd", "cmd": "cd {cwd} && git branch -v"},
        {"label": "stash list",  "id": "gstash",   "type": "cmd", "cmd": "cd {cwd} && git stash list"},
    ],
    "dev": [
        {"label": "python3 -V",    "id": "pyver",    "type": "cmd", "cmd": "python3 --version"},
        {"label": "pip list",       "id": "pipls",    "type": "cmd", "cmd": "python3 -m pip list --format=columns | head -30"},
        {"label": "npm ls",         "id": "npmls",    "type": "cmd", "cmd": "cd {cwd} && npm ls --depth=0 2>/dev/null || echo 'No package.json'"},
        {"label": "brew outdated",  "id": "brewout",  "type": "cmd", "cmd": "brew outdated"},
        {"label": "brew list",      "id": "brewls",   "type": "cmd", "cmd": "brew list --formula | head -30"},
        {"label": "which claude",   "id": "wclaude",  "type": "cmd", "cmd": "which claude && claude --version"},
    ],
    "term": [
        {"label": "tmux sessions",  "id": "tmuxls", "type": "cmd", "cmd": "tmux list-sessions 2>/dev/null || echo 'No sessions'"},
        {"label": "tmux windows",   "id": "tmuxw",  "type": "cmd", "cmd": "tmux list-windows -a 2>/dev/null || echo 'No windows'"},
        {"label": "who (logins)",   "id": "who",    "type": "cmd", "cmd": "who"},
    ],
    "claude": [
        {"label": "claude --version", "id": "cver",  "type": "cmd", "cmd": "claude --version 2>/dev/null || echo 'Claude CLI not found'"},
        {"label": "claude usage",     "id": "cinfo", "type": "info", "text": (
            "Claude AI commands:\n"
            "\u2022 /claude <prompt> \u2014 one-shot coding question\n"
            "\u2022 /chat \u2014 interactive back-and-forth mode\n"
            "\u2022 /exit \u2014 leave chat mode\n"
            "\u2022 /claude_continue \u2014 resume last session"
        )},
    ],
    "system": [
        {"label": "ps (top 15)",  "id": "ps",     "type": "cmd", "cmd": "ps aux | head -16"},
        {"label": "df (disk)",    "id": "df",     "type": "cmd", "cmd": "df -h"},
        {"label": "uptime",       "id": "uptime", "type": "cmd", "cmd": "uptime"},
        {"label": "top (snap)",   "id": "top",    "type": "cmd", "cmd": "top -l 1 -n 10 | head -22"},
    ],
    "net": [
        {"label": "ping 1.1.1.1", "id": "ping",   "type": "cmd", "cmd": "ping -c 3 1.1.1.1"},
        {"label": "tailscale",    "id": "ts",     "type": "cmd", "cmd": "tailscale status"},
        {"label": "netstat",      "id": "net",    "type": "cmd", "cmd": "netstat -an | grep LISTEN | head -15"},
        {"label": "ifconfig",     "id": "ifconf", "type": "cmd", "cmd": "ifconfig | grep -A 2 'inet '"},
    ],
    "apps": [
        {"label": "Running apps",    "id": "appls",   "type": "cmd", "cmd": "osascript -e 'tell application \"System Events\" to get name of every process whose background only is false'"},
        {"label": "Launch VS Code",  "id": "appvsc",  "type": "cmd", "cmd": "open -a 'Visual Studio Code'"},
        {"label": "Launch Finder",   "id": "appfind", "type": "cmd", "cmd": "open -a 'Finder'"},
    ],
}

# ── Lookups (built at import time) ───────────────────────────────────

# tool_id -> tool dict
_TOOL_BY_ID = {}
# callback_data ("tl:<id>") -> command template (for cmd-type tools only)
_TOOL_COMMANDS = {}

for _cat_id, _tools in CATEGORY_TOOLS.items():
    for _tool in _tools:
        _TOOL_BY_ID[_tool["id"]] = _tool
        if _tool["type"] == "cmd":
            _TOOL_COMMANDS[f"tl:{_tool['id']}"] = _tool["cmd"]


# ── Keyboard builders ────────────────────────────────────────────────

def _build_main_menu():
    """Build the 2-column category grid."""
    rows = []
    for i in range(0, len(CATEGORIES), 2):
        row = []
        for cat in CATEGORIES[i:i + 2]:
            row.append(InlineKeyboardButton(
                f"{cat['icon']} {cat['label']}",
                callback_data=f"tl:cat:{cat['id']}",
            ))
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def _build_category_page(cat_id):
    """Build a tool-button grid for a category + Back button."""
    tools = CATEGORY_TOOLS.get(cat_id, [])
    rows = []
    row = []
    for tool in tools:
        row.append(InlineKeyboardButton(
            tool["label"], callback_data=f"tl:{tool['id']}",
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("\u2b05 Back", callback_data="tl:back")])
    # Find category label for the header
    cat_label = cat_id
    for cat in CATEGORIES:
        if cat["id"] == cat_id:
            cat_label = f"{cat['icon']} {cat['label']}"
            break
    return cat_label, InlineKeyboardMarkup(rows)


# ── Handlers ─────────────────────────────────────────────────────────

@authorized
async def tools_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tools — show the category hub."""
    await update.message.reply_text(
        "Tool Hub \u2014 tap a category:",
        reply_markup=_build_main_menu(),
    )


async def tools_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all tl: callback queries (categories, back, tools)."""
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in AUTHORIZED_USER_IDS:
        await query.edit_message_text("Access denied.")
        return

    data = query.data

    # No-op (category headers in old layout — kept for safety)
    if data == "tl:noop":
        return

    # Back to main menu
    if data == "tl:back":
        await query.edit_message_text(
            "Tool Hub \u2014 tap a category:",
            reply_markup=_build_main_menu(),
        )
        return

    # Open a category page
    if data.startswith("tl:cat:"):
        cat_id = data[7:]  # strip "tl:cat:"
        if cat_id not in CATEGORY_TOOLS:
            await query.edit_message_text("Unknown category.")
            return
        cat_label, markup = _build_category_page(cat_id)
        await query.edit_message_text(
            f"{cat_label} \u2014 tap a tool:",
            reply_markup=markup,
        )
        return

    # Tool execution — strip "tl:" to get tool_id
    tool_id = data[3:]  # strip "tl:"
    tool = _TOOL_BY_ID.get(tool_id)
    if tool is None:
        await query.edit_message_text("Unknown tool action.")
        return

    # --- link type: show hint + Back ---
    if tool["type"] == "link":
        await query.edit_message_text(
            tool["text"],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("\u2b05 Back", callback_data="tl:back")],
            ]),
        )
        return

    # --- info type: show static text + Back ---
    if tool["type"] == "info":
        await query.edit_message_text(
            tool["text"],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("\u2b05 Back", callback_data="tl:back")],
            ]),
        )
        return

    # --- cmd type: run shell command ---
    cwd = get_working_dir(context)
    cmd = tool["cmd"].replace("{cwd}", cwd)

    await query.edit_message_text(f"Running: `{cmd}`...", parse_mode="Markdown")
    logger.info("Tool action by %s: %s", query.from_user.id, cmd)

    output, rc = await run_shell_command(cmd, timeout=30)
    output = scrub_output(output)

    prefix = "" if rc == 0 else f"[exit {rc}]\n"
    full_output = prefix + (output or "(no output)")

    chunks = chunk_text(full_output)
    await query.edit_message_text(f"```\n{chunks[0]}\n```", parse_mode="Markdown")
    for chunk in chunks[1:]:
        await query.message.reply_text(f"```\n{chunk}\n```", parse_mode="Markdown")
