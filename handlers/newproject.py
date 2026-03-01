from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from config import logger
from handlers.auth import authorized
from handlers.cd import DESKTOP


@authorized
async def newproject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /newproject <name> — create a project folder on Desktop."""
    if not context.args:
        await update.message.reply_text("Usage: /newproject <folder name>")
        return

    name = " ".join(context.args)

    # Security: reject path traversal, hidden dirs, slashes
    if "/" in name or "\\" in name or name.startswith(".") or ".." in name:
        await update.message.reply_text("Invalid folder name.")
        return

    folder = DESKTOP / name

    if folder.exists():
        await update.message.reply_text(
            f"Folder already exists: {folder}\n"
            "Send project.md content to overwrite, or /exit to cancel."
        )
    else:
        folder.mkdir(parents=False)
        await update.message.reply_text(
            f"Created: {folder}\nSend me the project.md content (plain text):"
        )

    # Store pending state — next plain text message will be saved as project.md
    context.user_data["pending_project_md"] = str(folder)


async def pending_project_md_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain text when we're waiting for project.md content."""
    folder_path = context.user_data.pop("pending_project_md", None)
    if folder_path is None:
        return
    folder = Path(folder_path)
    text = update.message.text

    project_file = folder / "project.md"
    project_file.write_text(text, encoding="utf-8")

    # Auto-cd into the new project
    context.user_data["working_dir"] = str(folder)

    await update.message.reply_text(
        f"Saved project.md ({len(text)} bytes).\n"
        f"Working dir set to:\n{folder}"
    )
    logger.info("User %s created project at %s", update.effective_user.id, folder)
