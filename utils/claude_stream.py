"""Parse stream-json output from Claude CLI and yield events.

Claude CLI with --output-format stream-json emits one JSON object per line.
Key message types:
  - {"type": "assistant", "message": {"type": "text", "text": "..."}}
  - {"type": "assistant", "message": {"type": "tool_use", "name": "...", "input": {...}}}
  - {"type": "result", "result": "...", "session_id": "..."}
"""

import json
from dataclasses import dataclass


@dataclass
class StreamEvent:
    kind: str    # "text", "tool_use", "thinking", "result", "error"
    data: str    # text content, tool description, or error message
    session_id: str = ""


def parse_stream_line(line: str) -> StreamEvent | None:
    """Parse a single stream-json line into a StreamEvent."""
    line = line.strip()
    if not line:
        return None

    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None

    msg_type = obj.get("type", "")

    # Result message — contains session_id
    if msg_type == "result":
        text = obj.get("result", "")
        sid = obj.get("session_id", "")
        # The result text may be in a subfield
        if isinstance(text, dict):
            text = text.get("text", str(text))
        return StreamEvent(kind="result", data=str(text), session_id=sid)

    # Assistant message subtypes
    message = obj.get("message", {})
    if isinstance(message, str):
        return StreamEvent(kind="text", data=message)

    content_type = message.get("type", "")

    if content_type == "text":
        return StreamEvent(kind="text", data=message.get("text", ""))

    if content_type == "tool_use":
        name = message.get("name", "unknown")
        tool_input = message.get("input", {})
        # Build a concise description
        if name in ("Edit", "Write") and "file_path" in tool_input:
            desc = f"{name}: `{tool_input['file_path']}`"
        elif name == "Read" and "file_path" in tool_input:
            desc = f"Reading `{tool_input['file_path']}`"
        elif name == "Bash" and "command" in tool_input:
            cmd = tool_input["command"][:80]
            desc = f"Running: `{cmd}`"
        elif name == "Glob" and "pattern" in tool_input:
            desc = f"Searching for `{tool_input['pattern']}`"
        elif name == "Grep" and "pattern" in tool_input:
            desc = f"Grepping for `{tool_input['pattern']}`"
        else:
            desc = f"Tool: {name}"
        return StreamEvent(kind="tool_use", data=desc)

    if content_type == "thinking":
        return StreamEvent(kind="thinking", data="")

    return None


def parse_stream_events(raw_output: str) -> tuple[list[StreamEvent], str]:
    """Parse all stream-json lines, return (events, session_id)."""
    events = []
    session_id = ""

    for line in raw_output.splitlines():
        event = parse_stream_line(line)
        if event:
            events.append(event)
            if event.session_id:
                session_id = event.session_id

    return events, session_id
