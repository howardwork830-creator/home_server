from telegram import Update
from telegram.ext import ContextTypes

from handlers.auth import authorized
from utils.subprocess_runner import run_shell_command


async def _section(label: str, command: str, timeout: int = 10) -> str:
    """Run a command and return a labelled section."""
    output, rc = await run_shell_command(command, timeout=timeout)
    if rc == 0 and output.strip():
        return f"{label}:\n{output.strip()}"
    return f"{label}: unavailable"


async def _battery() -> str:
    parts = []
    output, rc = await run_shell_command("pmset -g batt", timeout=10)
    if rc == 0:
        parts.append(f"Battery:\n{output.strip()}")
    else:
        parts.append("Battery: unavailable")

    output, rc = await run_shell_command(
        "system_profiler SPPowerDataType 2>/dev/null | head -30", timeout=15
    )
    if rc == 0 and output.strip():
        parts.append(f"Power Details:\n{output.strip()}")
    return "\n\n".join(parts)


async def _memory() -> str:
    parts = []
    output, rc = await run_shell_command("sysctl -n hw.memsize", timeout=5)
    if rc == 0:
        gb = int(output.strip()) / (1024 ** 3)
        parts.append(f"Total RAM: {gb:.1f} GB")

    output, rc = await run_shell_command("vm_stat", timeout=5)
    if rc == 0:
        parts.append(f"VM Stats:\n{output.strip()}")

    return "\n\n".join(parts) if parts else "Memory: unavailable"


async def _hardware() -> str:
    return await _section("Hardware", "system_profiler SPHardwareDataType", timeout=15)


async def _storage() -> str:
    parts = []
    output, rc = await run_shell_command("df -h", timeout=5)
    if rc == 0:
        parts.append(f"Disk Usage:\n{output.strip()}")

    output, rc = await run_shell_command(
        "system_profiler SPStorageDataType 2>/dev/null | head -40", timeout=15
    )
    if rc == 0 and output.strip():
        parts.append(f"Storage Details:\n{output.strip()}")

    return "\n\n".join(parts) if parts else "Storage: unavailable"


async def _overview() -> str:
    parts = []

    # Load average
    output, rc = await run_shell_command("sysctl -n vm.loadavg", timeout=5)
    if rc == 0:
        parts.append(f"Load: {output.strip()}")

    # Uptime
    output, rc = await run_shell_command("uptime", timeout=5)
    if rc == 0:
        parts.append(f"Uptime: {output.strip()}")

    # Hardware summary
    output, rc = await run_shell_command(
        "system_profiler SPHardwareDataType 2>/dev/null | grep -E 'Model Name|Chip|Total Number of Cores|Memory'",
        timeout=15,
    )
    if rc == 0 and output.strip():
        parts.append(f"Hardware:\n{output.strip()}")

    # Battery one-liner
    output, rc = await run_shell_command("pmset -g batt", timeout=5)
    if rc == 0:
        parts.append(f"Battery:\n{output.strip()}")

    # Disk summary
    output, rc = await run_shell_command("df -h /", timeout=5)
    if rc == 0:
        parts.append(f"Disk:\n{output.strip()}")

    return "\n\n".join(parts)


SUBSECTIONS = {
    "battery": _battery,
    "memory": _memory,
    "hardware": _hardware,
    "storage": _storage,
}


@authorized
async def sysinfo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sysinfo [subsection] — show detailed system information."""
    sub = (context.args[0].lower() if context.args else "").strip()

    if sub and sub not in SUBSECTIONS:
        options = ", ".join(sorted(SUBSECTIONS))
        await update.message.reply_text(f"Unknown subsection. Options: {options}")
        return

    if sub:
        body = await SUBSECTIONS[sub]()
    else:
        body = await _overview()

    await update.message.reply_text(f"```\n{body}\n```", parse_mode="Markdown")
