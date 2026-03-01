import shlex
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
from utils.audit import log_action
from utils.chunker import chunk_text
from utils.claude_stream import parse_stream_events
from utils.rate_limiter import rate_limiter
from utils.scrubber import scrub_output
from utils.subprocess_runner import run_shell_command


def _build_claude_command(prompt: str, session_id: str = "") -> str:
    """Build the Claude CLI command with all security flags."""
    escaped_prompt = shlex.quote(prompt)
    escaped_system = shlex.quote(CLAUDE_SYSTEM_PROMPT)

    parts = [
        "claude",
        "-p", escaped_prompt,
        "--allowedTools", shlex.quote(CLAUDE_ALLOWED_TOOLS),
        "--permission-mode", "plan",
        "--system-prompt", escaped_system,
        "--max-budget-usd", str(CLAUDE_MAX_BUDGET_USD),
        "--output-format", "stream-json",
    ]

    if session_id:
        parts.extend(["--resume", shlex.quote(session_id)])

    return " ".join(parts)


async def _run_claude_session(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    prompt: str,
    session_id: str = "",
) -> None:
    """Run a Claude session and stream results to Telegram."""
    user_id = update.effective_user.id

    # Rate limit check
    limit_msg = rate_limiter.check(user_id, "claude")
    if limit_msg:
        await update.message.reply_text(limit_msg)
        return

    logger.info("Claude request from %s: %s", user_id, prompt[:100])
    thinking_msg = await update.message.reply_text("Thinking...")
    start_time = time.monotonic()

    command = _build_claude_command(prompt, session_id)
    output, return_code = await run_shell_command(command, timeout=CLAUDE_TIMEOUT)

    duration = time.monotonic() - start_time

    # Delete the "Thinking..." message
    try:
        await thinking_msg.delete()
    except Exception:
        pass

    if return_code != 0:
        log_action(user_id, "claude", prompt, result="error", duration_s=duration)
        error_text = scrub_output(output[:500])
        await update.message.reply_text(f"Claude error (exit {return_code}):\n{error_text}")
        return

    # Parse stream-json output
    events, new_session_id = parse_stream_events(output)

    # Store session ID for continuation
    if new_session_id:
        context.user_data["claude_session_id"] = new_session_id

    # Build response from events
    text_parts: list[str] = []
    tool_summaries: list[str] = []

    for event in events:
        if event.kind == "text":
            text_parts.append(event.data)
        elif event.kind == "tool_use":
            tool_summaries.append(event.data)
        elif event.kind == "result" and event.data:
            text_parts.append(event.data)

    # If stream parsing yielded nothing, fall back to raw output
    full_text = "\n".join(text_parts).strip()
    if not full_text:
        full_text = output.strip()

    full_text = scrub_output(full_text)

    # Send tool activity summary if any
    if tool_summaries:
        summary = "\n".join(f"  {s}" for s in tool_summaries[:10])
        if len(tool_summaries) > 10:
            summary += f"\n  ... and {len(tool_summaries) - 10} more actions"
        await update.message.reply_text(f"Actions taken:\n{summary}")

    # Send response in chunks
    for chunk in chunk_text(full_text):
        await update.message.reply_text(chunk)

    log_action(user_id, "claude", prompt, result="ok", duration_s=duration)


@authorized
async def claude_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /claude <prompt> — full agent mode with controlled permissions."""
    if not context.args:
        await update.message.reply_text(
            "Usage: /claude <prompt>\n\n"
            "Example: /claude Write a Python hello world\n\n"
            "Claude can read, edit, and create files, run git commands, "
            "and execute Python scripts — with confirmation for destructive actions."
        )
        return

    prompt = " ".join(context.args)
    await _run_claude_session(update, context, prompt)


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
