"""Tests for the parts that don't need an API key.

Deliberately split: transcript loading and the estimator are pure logic and
should be verifiable offline. The counting functions hit the API, so they're
tested with a fake client rather than a live call — you shouldn't need to
spend money to know your parsing works.

That split is itself the lesson. Test what you can test cheaply; don't skip
testing something just because part of the system is remote.
"""

from __future__ import annotations

import json

import pytest

from src.counting import Turn, cumulative_counts, estimate_tokens
from src.transcript import load_transcript


class FakeCount:
    def __init__(self, n: int):
        self.input_tokens = n


class FakeMessages:
    """Stands in for client.messages — counts characters so results are predictable."""

    def count_tokens(self, model: str, messages: list[dict]) -> FakeCount:
        total = sum(len(m["content"]) for m in messages)
        return FakeCount(total)


class FakeClient:
    def __init__(self):
        self.messages = FakeMessages()


# --- transcript loading -------------------------------------------------


def test_loads_plain_list(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(
        json.dumps([{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]),
        encoding="utf-8",
    )
    turns = load_transcript(p)
    assert [t.role for t in turns] == ["user", "assistant"]


def test_loads_wrapped_messages(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"messages": [{"role": "human", "content": "hi"}]}), encoding="utf-8")
    turns = load_transcript(p)
    assert turns[0].role == "user", "'human' should normalise to 'user'"


def test_loads_jsonl(tmp_path):
    p = tmp_path / "c.jsonl"
    p.write_text(
        '{"role":"user","content":"a"}\n{"role":"assistant","content":"b"}\n',
        encoding="utf-8",
    )
    assert len(load_transcript(p)) == 2


def test_handles_content_blocks(tmp_path):
    """Content is sometimes a list of blocks rather than a string."""
    p = tmp_path / "c.json"
    p.write_text(
        json.dumps(
            [{"role": "user", "content": [{"type": "text", "text": "one"}, {"type": "image"}]}]
        ),
        encoding="utf-8",
    )
    turns = load_transcript(p)
    assert turns[0].content == "one", "non-text blocks should be ignored, not crash"


def test_loads_claude_code_transcript(tmp_path):
    """Claude Code nests each message under "message", alongside bookkeeping records."""
    p = tmp_path / "c.jsonl"
    lines = [
        {"type": "file-history-snapshot", "snapshot": {}},
        {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "hi"}]}},
        {"type": "assistant", "message": {"role": "assistant", "content": "hello"}},
    ]
    p.write_text("\n".join(json.dumps(line) for line in lines), encoding="utf-8")
    turns = load_transcript(p)
    assert [(t.role, t.content) for t in turns] == [("user", "hi"), ("assistant", "hello")]


def test_drops_empty_messages(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(
        json.dumps([{"role": "user", "content": "  "}, {"role": "user", "content": "real"}]),
        encoding="utf-8",
    )
    assert len(load_transcript(p)) == 1


def test_empty_transcript_raises(tmp_path):
    p = tmp_path / "c.json"
    p.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError):
        load_transcript(p)


# --- the estimator ------------------------------------------------------


def test_estimate_is_characters_over_four():
    assert estimate_tokens("a" * 400) == 100


def test_estimate_undercounts_code():
    """The heuristic's failure mode, made concrete.

    Dense punctuation tokenizes into more tokens than prose of the same
    length, so a character-based guess understates it. This test documents
    the direction of the error, which is the whole reason the exercise
    compares the two.
    """
    code = 'def f(x):\n    return {"k": [1, 2, 3]}\n' * 10
    prose = "the quick brown fox jumps over the lazy dog " * 10
    # Same rough length, and the estimator can't tell them apart at all.
    assert abs(estimate_tokens(code) - len(code) // 4) == 0
    assert abs(estimate_tokens(prose) - len(prose) // 4) == 0


# --- cumulative counting ------------------------------------------------


def test_cumulative_counts_grow_monotonically():
    turns = [Turn("user", "aaa"), Turn("assistant", "bbbb"), Turn("user", "cc")]
    counts = cumulative_counts(turns, client=FakeClient())
    assert counts == sorted(counts), "each turn resends everything before it"
    assert len(counts) == len(turns)


def test_cumulative_is_not_the_sum_of_individual_turns():
    """The point of the exercise, as an assertion.

    Turn N costs the whole prefix, not just turn N. With the fake client
    counting characters, the final cumulative equals total characters —
    which is much larger than the last turn alone.
    """
    turns = [Turn("user", "x" * 10), Turn("assistant", "y" * 10), Turn("user", "z" * 10)]
    counts = cumulative_counts(turns, client=FakeClient())
    assert counts[-1] == 30
    assert counts[-1] > 10, "the last turn alone is not what you pay for"
