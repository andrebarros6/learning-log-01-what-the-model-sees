"""Tests for the solution branch's analysis helpers."""

from src.analysis import biggest_jump, per_turn_deltas, turns_after_fraction
from src.counting import Turn


def _turns():
    return [Turn("user", "a"), Turn("assistant", "b" * 50), Turn("user", "c")]


def test_deltas_reconstruct_cumulative():
    cumulative = [10, 200, 210]
    jumps = per_turn_deltas(_turns(), cumulative)
    assert [j.added for j in jumps] == [10, 190, 10]
    assert jumps[-1].running_total == 210


def test_biggest_jump_finds_the_paste():
    jumps = per_turn_deltas(_turns(), [10, 200, 210])
    j = biggest_jump(jumps)
    assert j.index == 2 and j.added == 190


def test_biggest_jump_handles_empty():
    assert biggest_jump([]) is None


def test_turns_after_fraction():
    # Final total 210; half is 105, first crossed at turn 2.
    assert turns_after_fraction([10, 200, 210], 0.5) == 2
    assert turns_after_fraction([], 0.5) is None


def test_preview_is_truncated_and_single_line():
    turns = [Turn("user", "line one\nline two " + "x" * 200)]
    jumps = per_turn_deltas(turns, [100])
    assert "\n" not in jumps[0].preview
    assert len(jumps[0].preview) <= 71
