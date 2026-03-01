import asyncio
import os
import shlex
import signal
import time

from telegram import Update
from telegram.ext import ContextTypes

from config import (
    CLAUDE_ALLOWED_TOOLS,
    CLAUDE_MAX_BUDGET_USD,
    CLAUDE_SYSTEM_PROMPT,
    CLAUDE_TIMEOUT,
    logger,
)
from handlers.auth import authorized
from handlers.cd import get_working_dir
from utils.audit import log_action
from utils.chunker import chunk_text
from utils.claude_stream import parse_stream_line
from utils.rate_limiter import rate_limiter
from utils.scrubber import scrub_output

# How often (seconds) to flush buffered text to Telegram
_FLUSH_INTERVAL = 3.0


def _build_claude_command(prompt: str, session_id: str = "") -> str:
    """Build the Claude CLI command with all security flags."""
    escaped_prompt = shlex.quote(prompt)
    escaped_system = shlex.quote(CLAUDE_SYSTEM_PROMPT)

    parts = [
        "claude",
        "-p", escaped_prompt,
        "--allowedTools", shlex.quote(CLAUDE_ALLOWED_TOOLS),
        "--system-prompt", escaped_system,
        "--max-budget-usd", str(CLAUDE_MAX_BUDGET_USD),
        "--output-format", "stream-json",
        "--verbose",
    ]

    if session_id:
        parts.extend(["--resume", shlex.quote(session_id)])

    return " ".join(parts)


async def _send(update: Update, text: str) -> None:
    """Send text in chunks, swallowing Telegram errors."""
    text = scrub_output(text.strip())
    if not text:
        return
    for chunk in chunk_text(text):
        try:
            await update.message.reply_text(chunk)
        except Exception as e:
            logger.warning("Failed to send chunk: %s", e)


async def _run_claude_session(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    prompt: str,
    session_id: str = "",
) -> None:
    """Run a Claude session and stream results live to Telegram."""
    user_id = update.effective_user.id

    # Rate limit check
    limit_msg = rate_limiter.check(user_id, "claude")
    if limit_msg:
        await update.message.reply_text(limit_msg)
        return

    logger.info("Claude request from %s: %s", user_id, prompt[:100])
    status_msg = await update.message.reply_text("Starting Claude...")
    start_time = time.monotonic()

    command = _build_claude_command(prompt, session_id)
    cwd = get_working_dir(context)

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=cwd,
            preexec_fn=os.setsid,
        )
    except Exception as e:
        await status_msg.edit_text(f"Failed to start Claude: {e}")
        log_action(user_id, "claude", prompt, result="error")
        return

    # Delete the status message once output starts flowing
    status_deleted = False

    async def _delete_status():
        nonlocal status_deleted
        if not status_deleted:
            status_deleted = True
            try:
                await status_msg.delete()
            except Exception:
                pass

    # Read lines as they arrive and stream to Telegram
    new_session_id = ""
    text_buffer: list[str] = []
    last_flush = time.monotonic()

    async def _flush_text():
        nonlocal text_buffer, last_flush
        if text_buffer:
            await _delete_status()
            combined = "\n".join(text_buffer)
            text_buffer = []
            last_flush = time.monotonic()
            await _send(update, combined)

    try:
        async with asyncio.timeout(CLAUDE_TIMEOUT):
            while True:
                line = await process.stdout.readline()
                if not line:
                    break

                events = parse_stream_line(line.decode("utf-8", errors="replace"))
                for event in events:
                    if event.session_id:
                        new_session_id = event.session_id

                    if event.kind == "tool_use":
                        # Flush any buffered text first, then send tool activity
                        await _flush_text()
                        await _delete_status()
                        await _send(update, f">> {event.data}")

                    elif event.kind == "text" and event.data:
                        text_buffer.append(event.data)
                        # Flush periodically so user sees progress
                        if time.monotonic() - last_flush >= _FLUSH_INTERVAL:
                            await _flush_text()

                    elif event.kind == "result" and event.data:
                        text_buffer.append(event.data)

            # Wait for process to finish
            await process.wait()

    except TimeoutError:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
        await _flush_text()
        await _delete_status()
        await update.message.reply_text(f"Claude timed out after {CLAUDE_TIMEOUT}s.")
        log_action(user_id, "claude", prompt, result="timeout")
        return

    except Exception as e:
        logger.error("Claude streaming error: %s", e)
        await _flush_text()
        await _delete_status()
        await update.message.reply_text(f"Claude error: {e}")
        log_action(user_id, "claude", prompt, result="error")
        return

    # Flush remaining text
    await _flush_text()
    await _delete_status()

    duration = time.monotonic() - start_time
    return_code = process.returncode or 0

    # Store session ID for continuation
    if new_session_id:
        context.user_data["claude_session_id"] = new_session_id

    if return_code != 0:
        await update.message.reply_text(f"Claude exited with code {return_code}.")
        log_action(user_id, "claude", prompt, result="error", duration_s=duration)
    else:
        log_action(user_id, "claude", prompt, result="ok", duration_s=duration)


def is_chat_mode(context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if chat mode is active."""
    return context.user_data.get("claude_chat_mode", False)


@authorized
async def claude_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /claude <prompt> — full agent mode with controlled permissions."""
    if not context.args:
        await update.message.reply_text(
            "Usage: /claude <prompt>\n\n"
            "Example: /claude Write a Python hello world\n\n"
            "Claude can read, edit, and create files, run git commands, "
            "and execute Python scripts — with confirmation for destructive actions.\n\n"
            "Use /chat to enter interactive session mode."
        )
        return

    prompt = " ".join(context.args)
    await _run_claude_session(update, context, prompt)


@authorized
async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /chat — enter or start interactive Claude session mode."""
    if context.args:
        # /chat <prompt> starts a new session and enters chat mode
        context.user_data["claude_chat_mode"] = True
        prompt = " ".join(context.args)
        await update.message.reply_text("Chat mode ON. Send messages to talk to Claude.\nUse /exit to leave.")
        await _run_claude_session(update, context, prompt)
        return

    # /chat with no args — toggle on, using existing session if available
    context.user_data["claude_chat_mode"] = True
    session_id = context.user_data.get("claude_session_id", "")
    if session_id:
        await update.message.reply_text(
            "Chat mode ON (resuming session).\n"
            "Send messages to continue talking to Claude.\n"
            "Use /exit to leave."
        )
    else:
        await update.message.reply_text(
            "Chat mode ON.\n"
            "Send a message to start a Claude session.\n"
            "Use /exit to leave."
        )


@authorized
async def exit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /exit — leave chat mode."""
    if context.user_data.get("claude_chat_mode"):
        context.user_data["claude_chat_mode"] = False
        await update.message.reply_text("Chat mode OFF. Messages now go to shell.")
    else:
        await update.message.reply_text("Not in chat mode.")


async def chat_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain text messages when in chat mode — send to Claude."""
    prompt = update.message.text.strip()
    if not prompt:
        return

    session_id = context.user_data.get("claude_session_id", "")
    await _run_claude_session(update, context, prompt, session_id=session_id)


@authorized
async def claude_continue_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /claude_continue <prompt> — continue the last Claude session."""
    session_id = context.user_data.get("claude_session_id", "")
    if not session_id:
        await update.message.reply_text(
            "No previous Claude session to continue. Start one with /claude."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /claude_continue <follow-up prompt>\n\n"
            "Continues your last Claude conversation."
        )
        return

    prompt = " ".join(context.args)
    await _run_claude_session(update, context, prompt, session_id=session_id)
