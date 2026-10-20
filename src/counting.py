"""Token counting — the real thing, and the guess people use instead.

The whole point of this exercise is the gap between these two functions.
`estimate_tokens` is what most of us do in our heads. `count_tokens` asks
the API what the number actually is.

Run them against the same text and watch them disagree, especially on code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import cast

import anthropic
from anthropic.types import MessageParam

# The model whose tokenizer we're measuring against. Token counts are
# model-specific — a count for one model family is not a count for another,
# which is exactly why a generic tokenizer library is the wrong tool here.
DEFAULT_MODEL = "claude-opus-5"


@dataclass
class Turn:
    """One message in a conversation."""

    role: str
    content: str

    def to_message(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


def estimate_tokens(text: str) -> int:
    """The guess: four characters per token.

    This is the heuristic almost everyone uses, and it is wrong in a
    direction that matters. It was derived from English prose, so it
    under-counts precisely the content you care about — code, JSON,
    tables, non-English text.

    Included here so you can measure how wrong it is on your own data.
    Do not use it for anything real.
    """
    return len(text) // 4


def count_tokens(
    messages: list[dict[str, str]],
    model: str = DEFAULT_MODEL,
    client: anthropic.Anthropic | None = None,
) -> int:
    """The real number, from the API.

    This is a dedicated endpoint — it does not run inference, so it is
    cheap and fast. There is no reason to guess when this exists.
    """
    client = client or anthropic.Anthropic()
    # Turn.to_message() builds plain {"role", "content"} dicts — the shape
    # MessageParam describes. The cast says so to the type checker.
    result = client.messages.count_tokens(
        model=model, messages=cast("list[MessageParam]", messages)
    )
    return result.input_tokens


def count_turn(turn: Turn, model: str = DEFAULT_MODEL, client=None) -> int:
    """Token count for a single turn, measured on its own."""
    return count_tokens([turn.to_message()], model=model, client=client)


def cumulative_counts(
    turns: list[Turn],
    model: str = DEFAULT_MODEL,
    client: anthropic.Anthropic | None = None,
) -> list[int]:
    """What each turn ACTUALLY costs to send.

    This is the function that makes the point of the whole issue.

    A conversation is stateless: on turn N you resend turns 1..N in full.
    So the cost of turn N is not the size of turn N — it is the size of
    everything up to and including it. That is why long conversations get
    expensive and degrade, and why the growth curve is not a straight line.

    Returns one cumulative count per turn.
    """
    client = client or anthropic.Anthropic()
    counts: list[int] = []
    for i in range(1, len(turns) + 1):
        prefix = [t.to_message() for t in turns[:i]]
        counts.append(count_tokens(prefix, model=model, client=client))
    return counts


def context_window(model: str = DEFAULT_MODEL, client=None) -> int | None:
    """Ask the API how big this model's context window is.

    Deliberately not hardcoded. Context windows change between model
    versions; anything written down goes stale. Look it up instead —
    that habit is the durable skill, not the current number.

    Returns None if the running SDK doesn't expose the field yet.
    """
    client = client or anthropic.Anthropic()
    info = client.models.retrieve(model)
    return getattr(info, "max_input_tokens", None)


def require_api_key() -> None:
    """Fail early and clearly rather than deep inside an API call."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit(
            "ANTHROPIC_API_KEY is not set.\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...      (Windows: set ANTHROPIC_API_KEY=...)"
        )
