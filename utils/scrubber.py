from config import SECRET_PATTERNS


def scrub_output(text: str) -> str:
    """Redact secrets from text before sending to Telegram."""
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text
