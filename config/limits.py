"""Timeouts, rate limits, and size constraints."""

__all__ = [
    "COMMAND_TIMEOUT", "CLAUDE_TIMEOUT", "TAILSCALE_STATUS_TIMEOUT",
    "TELEGRAM_CHUNK_SIZE", "MAX_UPLOAD_SIZE", "MAX_OUTPUT_BYTES",
    "RATE_LIMIT_SHELL", "RATE_LIMIT_CLAUDE", "RATE_LIMIT_WINDOW",
    "MAX_TERMINALS",
    "POLLING_TIMEOUT", "POLLING_READ_TIMEOUT", "POLLING_CONNECT_TIMEOUT",
    "POLLING_WRITE_TIMEOUT", "POLLING_POOL_TIMEOUT", "POLLING_INTERVAL",
    "TCP_KEEPALIVE_IDLE",
]

# --- Timeouts ---
COMMAND_TIMEOUT = 300          # seconds
CLAUDE_TIMEOUT = 300           # seconds
TAILSCALE_STATUS_TIMEOUT = 5   # seconds

# --- Polling connection (Telegram long-poll) ---
POLLING_TIMEOUT = 10              # long-poll timeout sent to Telegram API
POLLING_READ_TIMEOUT = 15         # must be > POLLING_TIMEOUT (10s poll + 5s buffer)
POLLING_CONNECT_TIMEOUT = 10      # TCP connect timeout
POLLING_WRITE_TIMEOUT = 5         # HTTP write timeout
POLLING_POOL_TIMEOUT = 5          # connection pool wait timeout
POLLING_INTERVAL = 0.5            # pause between poll cycles
TCP_KEEPALIVE_IDLE = 60           # idle seconds before OS sends keepalive probes

# --- Telegram ---
TELEGRAM_CHUNK_SIZE = 4000     # chars per message

# --- Size limits ---
MAX_UPLOAD_SIZE = 20 * 1024 * 1024   # 20 MB
MAX_OUTPUT_BYTES = 50 * 1024         # 50 KB output cap

# --- Rate limits ---
RATE_LIMIT_SHELL = 20    # commands per minute
RATE_LIMIT_CLAUDE = 5    # requests per minute
RATE_LIMIT_WINDOW = 60   # sliding window in seconds

# --- Terminal sessions ---
MAX_TERMINALS = 3
