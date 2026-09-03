"""Find where a conversation's cost jumped, and why.

The cumulative chart shows growth. This finds the specific turn that caused
the biggest single increase — which, in a conversation that went wrong, is
very often the moment it did.
"""

from __future__ import annotations

from dataclasses import dataclass

from .counting import Turn


@dataclass
class Jump:
    """One turn's contribution to the total."""

    index: int          # 1-based, matching what the CLI prints
    role: str
    added: int          # tokens this turn added to the running total
    running_total: int
    preview: str

    def __str__(self) -> str:
        return (
            f"turn {self.index} ({self.role}) added {self.added:,} tokens "
            f"-> {self.running_total:,}\n    {self.preview}"
        )


def per_turn_deltas(turns: list[Turn], cumulative: list[int]) -> list[Jump]:
    """Convert cumulative counts into per-turn additions."""
    jumps: list[Jump] = []
    previous = 0
    for i, (turn, total) in enumerate(zip(turns, cumulative), start=1):
        preview = " ".join(turn.content.split())[:70]
        jumps.append(
            Jump(
                index=i,
                role=turn.role,
                added=total - previous,
                running_total=total,
                preview=preview + ("…" if len(turn.content) > 70 else ""),
            )
        )
        previous = total
    return jumps


def biggest_jump(jumps: list[Jump]) -> Jump | None:
    """The turn that cost the most. Usually a pasted file."""
    return max(jumps, key=lambda j: j.added) if jumps else None


def turns_after_fraction(cumulative: list[int], fraction: float) -> int | None:
    """First turn index where the conversation passed `fraction` of its final size.

    Useful for locating roughly where burial would have started, without
    needing to know the context window.
    """
    if not cumulative:
        return None
    threshold = cumulative[-1] * fraction
    for i, total in enumerate(cumulative, start=1):
        if total >= threshold:
            return i
    return None
