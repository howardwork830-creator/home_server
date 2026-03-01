import json
import time
from datetime import datetime, timezone

from config import AUDIT_LOG_FILE, logger


def log_action(
    user_id: int,
    action: str,
    prompt: str = "",
    result: str = "ok",
    duration_s: float = 0.0,
) -> None:
    """Append a structured audit entry to audit.jsonl.

    Never logs command output (could contain secrets).
    """
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "action": action,
        "prompt": prompt[:200],  # cap prompt length in log
        "result": result,
        "duration_s": round(duration_s, 2),
    }
    try:
        with open(AUDIT_LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error("Failed to write audit log: %s", e)
