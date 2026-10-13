"""Game rules and state for playing a puzzle; no input/output happens here."""
from __future__ import annotations

from typing import List, Tuple

from .board import (
    CELL_COUNT,
    PEERS,
    SIZE,
    Board,
    SudokuError,
    cell_name,
    index_of,
)
from .solver import count_solutions, solve
from .techniques import next_step


class MoveError(SudokuError):
    """The requested move is not allowed."""


class Game:
    """A puzzle in progress with undo, hints and mistake checking."""

    def __init__(self, puzzle: Board) -> None:
        puzzle.validate()
        if count_solutions(puzzle, limit=2) != 1:
            raise SudokuError("a playable puzzle must have exactly one solution")
        self.solution = solve(puzzle).solution
        self.board = puzzle.copy()
        self.givens = frozenset(i for i in range(CELL_COUNT) if puzzle[i])
        self.moves = 0
        self.hints_used = 0
        self._history: List[Tuple[int, int]] = []  # (index, previous value)

    @staticmethod
    def _locate(row: int, col: int) -> int:
        """Convert one-based (row, col) typed by a player to a flat index."""
        if not (1 <= row <= SIZE and 1 <= col <= SIZE):
            raise MoveError(f"row and column must be between 1 and {SIZE}")
        return index_of(row - 1, col - 1)

    def place(self, row: int, col: int, value: int) -> List[int]:
        """Put ``value`` in a cell (one-based coordinates).

        Returns the indices of peers that already hold the same digit; the
        move is still made so the player can see and fix the clash.
        """
        index = self._locate(row, col)
        if not 1 <= value <= SIZE:
            raise MoveError(f"digit must be between 1 and {SIZE}")
        if index in self.givens:
            raise MoveError(f"{cell_name(index)} is part of the puzzle and cannot be changed")
        self._history.append((index, self.board[index]))
        self.board[index] = value
        self.moves += 1
        return sorted(p for p in PEERS[index] if self.board[p] == value)

    def clear(self, row: int, col: int) -> None:
        index = self._locate(row, col)
        if index in self.givens:
            raise MoveError(f"{cell_name(index)} is part of the puzzle and cannot be changed")
        if self.board[index] == 0:
            raise MoveError(f"{cell_name(index)} is already empty")
        self._history.append((index, self.board[index]))
        self.board[index] = 0
        self.moves += 1

    def undo(self) -> str:
        """Take back the last move and describe what was restored."""
        if not self._history:
            raise MoveError("nothing to undo")
        index, previous = self._history.pop()
        self.board[index] = previous
        self.moves = max(0, self.moves - 1)
        return f"{cell_name(index)} is now {previous if previous else 'empty'}"

    def wrong_cells(self) -> List[int]:
        """Player-filled cells that differ from the solution."""
        return [
            i for i in range(CELL_COUNT)
            if i not in self.givens and self.board[i] and self.board[i] != self.solution[i]
        ]

    def hint(self) -> str:
        """Advice for the next move. It never fills a cell for the player."""
        self.hints_used += 1
        wrong = self.wrong_cells()
        if wrong:
            return f"{cell_name(wrong[0])} looks wrong, try clearing it."
        step = next_step(self.board)
        if step is not None:
            return str(step)
        for index in self.board.empty_indices():
            return f"No simple deduction left. Try {cell_name(index)} = {self.solution[index]}."
        return "The grid is full, nothing left to hint."

    def is_won(self) -> bool:
        return self.board.is_solved()
