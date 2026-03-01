"""Parse stream-json output from Claude CLI and yield events.

Claude CLI with --output-format stream-json --verbose emits one JSON object per line.
Key message types:
  - {"type": "assistant", "message": {"content": [{"type": "text", "text": "..."}]}, "session_id": "..."}
  - {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "...", "input": {...}}]}, ...}
  - {"type": "result", "result": "...", "session_id": "..."}
"""

import json
from dataclasses import dataclass


@dataclass
class StreamEvent:
    kind: str    # "text", "tool_use", "thinking", "result", "error"
    data: str    # text content, tool description, or error message
    session_id: str = ""


def _describe_tool(name: str, tool_input: dict) -> str:
    """Build a concise human-readable description of a tool use."""
    if name in ("Edit", "Write") and "file_path" in tool_input:
        return f"{name}: `{tool_input['file_path']}`"
    if name == "Read" and "file_path" in tool_input:
        return f"Reading `{tool_input['file_path']}`"
    if name == "Bash" and "command" in tool_input:
        cmd = tool_input["command"][:80]
        return f"Running: `{cmd}`"
    if name == "Glob" and "pattern" in tool_input:
        return f"Searching for `{tool_input['pattern']}`"
    if name == "Grep" and "pattern" in tool_input:
        return f"Grepping for `{tool_input['pattern']}`"
    return f"Tool: {name}"


def parse_stream_line(line: str) -> list[StreamEvent]:
    """Parse a single stream-json line into StreamEvent(s).

    Returns a list because one assistant message can contain multiple
    content blocks (e.g. thinking + text, or text + tool_use).
    """
    line = line.strip()
    if not line:
        return []

    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return []

    msg_type = obj.get("type", "")
    sid = obj.get("session_id", "")

    # Result message
    if msg_type == "result":
        text = obj.get("result", "")
        if isinstance(text, dict):
            text = text.get("text", str(text))
        return [StreamEvent(kind="result", data=str(text), session_id=sid)]

    # Assistant message — content is an array of blocks
    if msg_type == "assistant":
        message = obj.get("message", {})
        if not isinstance(message, dict):
            return []

        content = message.get("content", [])
        if not isinstance(content, list):
            return []

        events = []
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type", "")

            if block_type == "text":
                text = block.get("text", "")
                if text:
                    events.append(StreamEvent(kind="text", data=text, session_id=sid))

            elif block_type == "tool_use":
                name = block.get("name", "unknown")
                tool_input = block.get("input", {})
                desc = _describe_tool(name, tool_input)
                events.append(StreamEvent(kind="tool_use", data=desc, session_id=sid))

            elif block_type == "thinking":
                events.append(StreamEvent(kind="thinking", data="", session_id=sid))

        return events

    return []


def parse_stream_events(raw_output: str) -> tuple[list[StreamEvent], str]:
    """Parse all stream-json lines, return (events, session_id)."""
    events = []
    session_id = ""

    for line in raw_output.splitlines():
        for event in parse_stream_line(line):
            events.append(event)
            if event.session_id:
                session_id = event.session_id

    return events, session_id
