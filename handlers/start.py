from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from handlers.auth import authorized

HELP_TEXT = """Available commands:

/start — Show main menu
/help — This message
/status — System status (uptime, disk, Tailscale)
/network — Network diagnostics (IPs, connectivity, VPN)
/claude <prompt> — Ask Claude a question
/claude_continue <prompt> — Continue the last Claude conversation
/t — List persistent terminal sessions
/t new [name] — Create a new terminal (max 3)
/t <id> — Switch active terminal
/t close <id> — Close a terminal
/tmux ls — List tmux sessions
/tmux send <session> <command> — Send command to tmux session
/cd — Select project directory (Desktop folders)
/newproject <name> — Create a new project folder on Desktop
/chat — Enter Claude chat mode (back-and-forth coding)
/exit — Leave chat mode
/getfile <path> — Download a file from server to Telegram
/app — List/launch/quit applications
/sysinfo — Detailed system info (battery, memory, hardware, storage)
/monitor — Open live screen monitor (via Telegram Mini App)

Persistent terminals: Commands run in tmux-backed sessions. cd, env vars, and state persist between commands. Type "exit" to close the active terminal.

Plain text — Executed as a shell command (72 allowlisted commands)
Document upload — Saved to the working directory

Allowed shell commands (72):

Core: ls, pwd, cat, head, tail, grep, find, echo, wc, sort, tree, which, file, du, date, whoami
Dev: python3, npm, npx, git, tmux, claude
Files: open
System: ps, df, uptime, sw_vers, system_profiler, uname, hostname, top, pgrep, kill, killall
Network: ping, traceroute, dig, nslookup, netstat, lsof, ifconfig, networksetup, networkQuality, curl, wget, tailscale
Disk: diskutil, hdiutil, tmutil
Packages: brew, softwareupdate, pkgutil, xcode-select
Media: afplay, say, sips, screencapture
Text: sed, awk, uniq, pbcopy, pbpaste
Compression: tar, gzip, gunzip, zip, unzip
Automation: shortcuts, caffeinate
Utilities: trash, mdfind, mdls

Dangerous commands (rm -rf, sudo, etc.) are blocked. Some commands require specific flags (e.g. ping -c, top -l)."""


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
