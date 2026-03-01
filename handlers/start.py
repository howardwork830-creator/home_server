from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from handlers.auth import authorized

KEYBOARD = ReplyKeyboardMarkup(
    [
        ["Shell", "Claude"],
        ["Files", "Git"],
        ["Status", "tmux"],
        ["CD", "Chat"],
        ["New Project"],
    ],
    resize_keyboard=True,
)

HELP_TEXT = """Available commands:

/start — Show main menu
/help — This message
/status — System status (uptime, disk, Tailscale)
/claude <prompt> — Ask Claude a question
/claude_continue <prompt> — Continue the last Claude conversation
/tmux ls — List tmux sessions
/tmux send <session> <command> — Send command to tmux session
/cd — Select project directory (Desktop folders)
/newproject <name> — Create a new project folder on Desktop
/chat — Enter Claude chat mode (back-and-forth coding)
/exit — Leave chat mode

Plain text — Executed as a shell command (allowlisted commands only)
Document upload — Saved to the working directory

Allowed shell commands: ls, pwd, cat, head, tail, grep, find, ps, df, uptime, echo, wc, sort, tree, which, file, du, date, whoami, python3, git, tmux, tailscale, claude

Dangerous commands (rm -rf, sudo, etc.) are blocked."""


@authorized
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to your Mac M1 Home Server Bot!\n\n"
        "Send any allowlisted shell command as plain text, "
        "or use the menu buttons below.\n\n"
        "Type /help for details.",
        reply_markup=KEYBOARD,
    )


@authorized
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)
