"""Measure what a conversation actually costs to send.

    python -m src.main data/example-conversation.json

Then run it against your own export. The example is here so the repo works
out of the box; it isn't the point. Your own longest chat is the point.
"""

from __future__ import annotations

import argparse

from .counting import (
    DEFAULT_MODEL,
    context_window,
    cumulative_counts,
    count_turn,
    estimate_tokens,
    require_api_key,
)
from .transcript import load_transcript

BAR_WIDTH = 40


def _bar(value: int, peak: int, width: int = BAR_WIDTH) -> str:
    """A chart you can read in a terminal, with no plotting dependency."""
    if peak <= 0:
        return ""
    return "█" * max(1, round(value / peak * width))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transcript", help="Path to a conversation export (.json or .jsonl)")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    require_api_key()

    turns = load_transcript(args.transcript)
    print(f"Loaded {len(turns)} turns from {args.transcript}\n")

    print("Counting… (one API call per turn)\n")
    cumulative = cumulative_counts(turns, model=args.model)
    peak = cumulative[-1]

    # Step 1 + 2: what each turn costs to SEND, and how that grows.
    print(f"{'turn':>4}  {'role':<9} {'this turn':>9} {'sent':>8}  growth")
    print("-" * 78)
    for i, (turn, total) in enumerate(zip(turns, cumulative), start=1):
        own = count_turn(turn, model=args.model)
        print(f"{i:>4}  {turn.role:<9} {own:>9} {total:>8}  {_bar(total, peak)}")

    # Step 4: the heuristic everyone uses, against the truth.
    full_text = "\n".join(t.content for t in turns)
    guess = estimate_tokens(full_text)
    actual = peak
    delta = actual - guess
    pct = (delta / actual * 100) if actual else 0.0

    print("\n" + "=" * 78)
    print("The guess vs the number")
    print("=" * 78)
    print(f"  len(text)/4 estimate : {guess:>9,}")
    print(f"  actual (API)         : {actual:>9,}")
    print(f"  off by               : {delta:>+9,}  ({pct:+.1f}% of actual)")

    if abs(pct) > 10:
        print("\n  That gap is why you measure instead of estimating.")
        print("  It gets worse with code, JSON, tables, and non-English text.")

    window = context_window(args.model)
    if window:
        used = actual / window * 100
        print(f"\n  {args.model} context window: {window:,} tokens")
        print(f"  This conversation uses {used:.1f}% of it.")
        if used > 50:
            print("  Over half the window is history. That is where burial starts.")

    print("\nNow run it on your own longest working chat.")
    print("Nothing here lands until you see your own number.")


if __name__ == "__main__":
    main()
