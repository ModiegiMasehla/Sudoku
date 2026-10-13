"""Human-style solving techniques that explain every deduction they make."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from .board import DIGITS, UNITS, Board, cell_name

Candidates = Dict[int, Set[int]]

NAKED_SINGLE = "Naked single"
HIDDEN_SINGLE = "Hidden single"


@dataclass(frozen=True)
class Step:
    """One deduction: put ``value`` in cell ``index`` and why."""

    technique: str
    index: int
    value: int
    reason: str

    def __str__(self) -> str:
        return f"{self.technique}: {self.reason}"


def candidate_map(board: Board) -> Candidates:
    """Candidates for every empty cell, computed once per call."""
    return {i: board.candidates(i) for i in board.empty_indices()}


def has_dead_end(candidates: Candidates) -> bool:
    """True if some empty cell has no legal digit left (a contradiction)."""
    return any(not c for c in candidates.values())


def find_naked_single(board: Board, candidates: Optional[Candidates] = None) -> Optional[Step]:
    """A cell whose row, column and box already rule out all but one digit."""
    cands = candidate_map(board) if candidates is None else candidates
    for index in sorted(cands):
        if len(cands[index]) == 1:
            (value,) = cands[index]
            reason = (
                f"{cell_name(index)} can only be {value}, "
                f"every other digit is already in its row, column or box"
            )
            return Step(NAKED_SINGLE, index, value, reason)
    return None


def find_hidden_single(board: Board, candidates: Optional[Candidates] = None) -> Optional[Step]:
    """A digit that has only one possible cell left inside a row, column or box."""
    cands = candidate_map(board) if candidates is None else candidates
    for kind, number, cells in UNITS:
        placed = {board[i] for i in cells if board[i]}
        for digit in DIGITS:
            if digit in placed:
                continue
            spots = [i for i in cells if i in cands and digit in cands[i]]
            if len(spots) == 1:
                index = spots[0]
                reason = (
                    f"in {kind} {number}, {digit} can only go in {cell_name(index)}"
                )
                return Step(HIDDEN_SINGLE, index, digit, reason)
    return None


def next_step(board: Board) -> Optional[Step]:
    """The easiest available deduction, or None if the techniques are stuck."""
    cands = candidate_map(board)
    if has_dead_end(cands):
        return None
    return find_naked_single(board, cands) or find_hidden_single(board, cands)


def apply_logic(board: Board) -> List[Step]:
    """Apply techniques to ``board`` in place until none applies.

    Each step is found against the *current* grid, so a deduction can never
    rely on a stale candidate list. Returns the steps in the order applied.
    """
    steps: List[Step] = []
    while True:
        step = next_step(board)
        if step is None:
            return steps
        board[step.index] = step.value
        steps.append(step)
