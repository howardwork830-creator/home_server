import asyncio
import os
import signal

from config import COMMAND_TIMEOUT, MAX_OUTPUT_BYTES, WORK_DIR, logger


async def run_shell_command(
    command: str,
    timeout: int = COMMAND_TIMEOUT,
    cwd: str | None = None,
) -> tuple[str, int]:
    """Run a shell command asynchronously with timeout and process-group kill.

    Returns (output, return_code). Output combines stdout and stderr.
    Output is truncated at MAX_OUTPUT_BYTES to prevent memory issues.
    """
    work_dir = cwd or str(WORK_DIR)

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=work_dir,
            preexec_fn=os.setsid,
        )

        try:
            stdout, _ = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            # Truncate output at MAX_OUTPUT_BYTES
            truncated = False
            if len(stdout) > MAX_OUTPUT_BYTES:
                stdout = stdout[:MAX_OUTPUT_BYTES]
                truncated = True

            output = stdout.decode("utf-8", errors="replace").strip()

            if truncated:
                output += f"\n\n[Output truncated at {MAX_OUTPUT_BYTES // 1024}KB]"

            return (output or "(no output)", process.returncode or 0)

        except asyncio.TimeoutError:
            # Kill the entire process group
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
            logger.warning("Command timed out after %ds: %s", timeout, command)
            return (f"Command timed out after {timeout}s.", -1)

    except Exception as e:
        logger.error("Failed to run command: %s — %s", command, e)
        return (f"Error: {e}", -1)
