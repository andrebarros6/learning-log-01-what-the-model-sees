"""Load a conversation from disk.

Exports differ by product and change without warning, so this accepts a few
shapes rather than one. If yours isn't handled, add a branch — that's a
legitimate part of the exercise, not a detour from it.
"""

from __future__ import annotations

import json
from pathlib import Path

from .counting import Turn

_ROLE_ALIASES = {
    "human": "user",
    "user": "user",
    "assistant": "assistant",
    "ai": "assistant",
    "model": "assistant",
    "bot": "assistant",
}


def _normalise_role(raw: str) -> str:
    """Map whatever the export calls a role onto user/assistant."""
    return _ROLE_ALIASES.get(str(raw).strip().lower(), "user")


def _extract_text(content) -> str:
    """Pull plain text out of a content field.

    Content is sometimes a string and sometimes a list of blocks. Handle
    both, and ignore non-text blocks (images, tool calls) — they have token
    costs this exercise does not try to model.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts)
    return ""


def load_transcript(path: str | Path) -> list[Turn]:
    """Read a conversation export into a list of turns.

    Accepts:
      - a JSON list of {role, content}
      - {"messages": [...]}  or  {"conversation": [...]}
      - JSONL, one message per line

    Empty messages are dropped: they add nothing and distort the chart.
    """
    path = Path(path)
    raw = path.read_text(encoding="utf-8").strip()

    if path.suffix == ".jsonl":
        records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    else:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            records = (
                parsed.get("messages")
                or parsed.get("conversation")
                or parsed.get("chat_messages")
                or []
            )
        else:
            records = parsed

    turns: list[Turn] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        text = _extract_text(record.get("content", record.get("text", "")))
        if not text.strip():
            continue
        turns.append(Turn(role=_normalise_role(record.get("role", "user")), content=text))

    if not turns:
        raise ValueError(
            f"No messages found in {path}. "
            "Check the export shape and add a branch to load_transcript if needed."
        )
    return turns
