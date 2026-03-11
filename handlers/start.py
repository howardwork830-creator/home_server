from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from handlers.auth import authorized

HELP_TEXT = """Available commands (all menu-driven — just tap!):

📂 Files & Navigation
/cd — Browse files & folders (tap to navigate, download, view info)
/getfile <path> — Download a file (or use /cd to browse & tap)
/newproject <name> — Create a new project folder on Desktop
/tools — Quick tools (common shell commands as buttons)

🤖 Claude AI
/claude <prompt> — Ask Claude a question
/chat — Enter interactive chat mode
/exit — Leave chat mode
/claude_continue — Continue last conversation

💻 Terminals
/t — Manage terminals (tap to switch, create, close)
/tmux — Manage tmux sessions

📊 System & Monitoring
/status — System status
/sysinfo — Detailed system info
/network — Network diagnostics
/monitor — Live screen monitor
/app — Applications (tap to launch/quit)
/steam — Steam Remote Play (tap controls)

Plain text — Executed as a shell command (72 allowlisted commands)
Document upload — Saved to the working directory"""


@authorized
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to your Mac M1 Home Server Bot!\n\n"
        "Send any shell command as plain text (e.g. `ls`, `git status`).\n"
        "Tap the menu button or type `/` to see all commands.\n\n"
        "Type /help for details.",
        reply_markup=ReplyKeyboardRemove(),
    )


@authorized
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)
