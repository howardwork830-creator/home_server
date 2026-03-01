import time
from collections import defaultdict

from config import RATE_LIMIT_SHELL, RATE_LIMIT_CLAUDE, RATE_LIMIT_WINDOW


class RateLimiter:
    """Sliding window rate limiter keyed by (user_id, action)."""

    def __init__(self):
        # {(user_id, action): [timestamp, ...]}
        self._hits: dict[tuple[int, str], list[float]] = defaultdict(list)

    def _prune(self, key: tuple[int, str], now: float) -> None:
        """Remove timestamps outside the sliding window."""
        cutoff = now - RATE_LIMIT_WINDOW
        self._hits[key] = [t for t in self._hits[key] if t > cutoff]

    def check(self, user_id: int, action: str) -> str | None:
        """Check if user is rate-limited for the given action.

        Returns a cooldown message if limited, None if allowed.
        Records the hit if allowed.
        """
        if action == "claude":
            limit = RATE_LIMIT_CLAUDE
        else:
            limit = RATE_LIMIT_SHELL

        key = (user_id, action)
        now = time.monotonic()
        self._prune(key, now)

        if len(self._hits[key]) >= limit:
            return f"Rate limited: max {limit} {action} requests per minute. Please wait."

        self._hits[key].append(now)
        return None


# Singleton instance
rate_limiter = RateLimiter()
