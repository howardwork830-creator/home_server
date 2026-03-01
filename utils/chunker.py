from config import TELEGRAM_CHUNK_SIZE


def chunk_text(text: str, max_len: int = TELEGRAM_CHUNK_SIZE) -> list[str]:
    """Split text into chunks that fit within Telegram's message limit.

    Splits on newline boundaries when possible, hard-splits otherwise.
    """
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break

        # Try to split at a newline
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            # No newline found — hard split
            split_at = max_len

        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")

    return chunks
