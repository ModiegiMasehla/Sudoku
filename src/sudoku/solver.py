"""Complete solver: bitmask backtracking with a fewest-candidates-first heuristic."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional

from .board import (
    BOX_SIZE,
    CELL_COUNT,
    DIGITS,
    SIZE,
    Board,
    SudokuError,
    box_of,
    col_of,
    row_of,
)
from .techniques import Step, apply_logic

_ALL_DIGITS_MASK = sum(1 << d for d in DIGITS)


class UnsolvableError(SudokuError):
    """The puzzle follows the rules but has no solution."""


@dataclass(frozen=True)
class SolveResult:
    """Outcome of :func:`solve`.

    ``steps`` are the human-style deductions available from the starting
    grid. ``guesses`` counts trial placements the search needed on the way to
    the solution, and ``unique`` says whether the solution is the only one.
    """

    solution: Board
    steps: List[Step]
    guesses: int
    unique: bool
    solved_by_logic: bool


class _Search:
    """Depth-first search using one bitmask per row, column and box."""

    def __init__(self, board: Board, rng: Optional[random.Random] = None) -> None:
        self.cells = board.to_list()
        self.rows = [0] * SIZE
        self.cols = [0] * SIZE
        self.boxes = [0] * SIZE
        for i, v in enumerate(self.cells):
            if v:
                self._mark(i, v)
        self.rng = rng
        self.found = 0
        self.first: Optional[List[int]] = None
        self.guesses = 0
        self.guesses_to_first = 0

    def _mark(self, i: int, v: int) -> None:
        bit = 1 << v
        self.rows[row_of(i)] |= bit
        self.cols[col_of(i)] |= bit
        self.boxes[box_of(i)] |= bit

    def _unmark(self, i: int, v: int) -> None:
        bit = ~(1 << v)
        self.rows[row_of(i)] &= bit
        self.cols[col_of(i)] &= bit
        self.boxes[box_of(i)] &= bit

    def _most_constrained(self):
        """Empty cell with the fewest candidates, or None if the grid is full."""
        best_index, best_mask, best_count = -1, 0, SIZE + 1
        for i in range(CELL_COUNT):
            if self.cells[i]:
                continue
            used = self.rows[row_of(i)] | self.cols[col_of(i)] | self.boxes[box_of(i)]
            mask = _ALL_DIGITS_MASK & ~used
            count = bin(mask).count("1")
            if count < best_count:
                best_index, best_mask, best_count = i, mask, count
                if count <= 1:  # forced move or dead end, cannot do better
                    break
        return None if best_index < 0 else (best_index, best_mask, best_count)

    def run(self, limit: int) -> None:
        """Search until ``limit`` solutions have been found (or none remain)."""
        self._dfs(limit)

    def _dfs(self, limit: int) -> bool:
        """Returns True when the search should stop early."""
        pick = self._most_constrained()
        if pick is None:
            self.found += 1
            if self.first is None:
                self.first = self.cells[:]
                self.guesses_to_first = self.guesses
            return self.found >= limit
        index, mask, count = pick
        digits = [d for d in DIGITS if mask & (1 << d)]
        if self.rng is not None:
            self.rng.shuffle(digits)
        for digit in digits:
            if count > 1:
                self.guesses += 1
            self.cells[index] = digit
            self._mark(index, digit)
            stop = self._dfs(limit)
            self.cells[index] = 0
            self._unmark(index, digit)
            if stop:
                return True
        return False


def count_solutions(board: Board, limit: int = 2) -> int:
    """Number of solutions, counting no further than ``limit``.

    A grid that already breaks the rules has zero solutions.
    """
    if not board.is_valid():
        return 0
    search = _Search(board)
    search.run(limit)
    return search.found


def solve(board: Board) -> SolveResult:
    """Solve a puzzle completely.

    Raises :class:`InvalidPuzzleError` if the givens break the rules and
    :class:`UnsolvableError` if no solution exists. The input is not modified.
    """
    board.validate()
    search = _Search(board)
    search.run(limit=2)
    if search.first is None:
        raise UnsolvableError("the puzzle has no solution")
    logic = board.copy()
    steps = apply_logic(logic)
    return SolveResult(
        solution=Board(search.first),
        steps=steps,
        guesses=search.guesses_to_first,
        unique=search.found == 1,
        solved_by_logic=logic.is_complete(),
    )


def random_solution(rng: Optional[random.Random] = None) -> Board:
    """A uniformly shuffled, completely filled valid grid."""
    search = _Search(Board(), rng or random.Random())
    search.run(limit=1)
    assert search.first is not None
    return Board(search.first)
