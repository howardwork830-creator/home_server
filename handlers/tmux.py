import shlex

from telegram import Update
from telegram.ext import ContextTypes

from handlers.auth import authorized
from utils.subprocess_runner import run_shell_command


@authorized
async def tmux_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []

    if not args:
        await update.message.reply_text(
            "Usage:\n"
            "/tmux ls — list sessions\n"
            "/tmux send <session> <command> — send command to session"
        )
        return

    subcmd = args[0]

    if subcmd == "ls":
        output, _ = await run_shell_command("tmux list-sessions")
        await update.message.reply_text(f"```\n{output}\n```", parse_mode="Markdown")

    elif subcmd == "send" and len(args) >= 3:
        session = shlex.quote(args[1])
        keys = " ".join(args[2:])
        escaped_keys = shlex.quote(keys)
        cmd = f"tmux send-keys -t {session} {escaped_keys} Enter"
        output, rc = await run_shell_command(cmd)
        if rc == 0:
            await update.message.reply_text(f"Sent to session `{args[1]}`.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"Error:\n```\n{output}\n```", parse_mode="Markdown")

    else:
        await update.message.reply_text(
            "Unknown tmux subcommand. Use `ls` or `send <session> <cmd>`."
        )
