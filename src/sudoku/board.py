"""Board model: parsing, validation, candidate computation and formatting."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, NamedTuple, Optional, Sequence, Set, Tuple, Union

SIZE = 9
BOX_SIZE = 3
CELL_COUNT = SIZE * SIZE
DIGITS = tuple(range(1, SIZE + 1))

_BLANK_CHARS = "0._"
_IGNORED_CHARS = "|-+"


class SudokuError(ValueError):
    """Base class for every error raised by this package."""


class ParseError(SudokuError):
    """The text could not be read as a 9x9 grid."""


class InvalidPuzzleError(SudokuError):
    """The grid breaks the Sudoku rules (a digit repeats in a unit)."""


def index_of(row: int, col: int) -> int:
    """Flat index of a zero-based (row, col) pair."""
    if not (0 <= row < SIZE and 0 <= col < SIZE):
        raise IndexError(f"row and column must be 0-{SIZE - 1}, got ({row}, {col})")
    return row * SIZE + col


def row_of(index: int) -> int:
    return index // SIZE


def col_of(index: int) -> int:
    return index % SIZE


def box_of(index: int) -> int:
    return (row_of(index) // BOX_SIZE) * BOX_SIZE + col_of(index) // BOX_SIZE


def cell_name(index: int) -> str:
    """Human-friendly one-based name, e.g. index 0 -> 'R1C1'."""
    return f"R{row_of(index) + 1}C{col_of(index) + 1}"


def _build_units() -> List[Tuple[str, int, Tuple[int, ...]]]:
    units: List[Tuple[str, int, Tuple[int, ...]]] = []
    for r in range(SIZE):
        units.append(("row", r + 1, tuple(r * SIZE + c for c in range(SIZE))))
    for c in range(SIZE):
        units.append(("column", c + 1, tuple(r * SIZE + c for r in range(SIZE))))
    for b in range(SIZE):
        top, left = (b // BOX_SIZE) * BOX_SIZE, (b % BOX_SIZE) * BOX_SIZE
        cells = tuple(
            (top + r) * SIZE + left + c for r in range(BOX_SIZE) for c in range(BOX_SIZE)
        )
        units.append(("box", b + 1, cells))
    return units


#: Every row, column and box as ``(kind, one-based number, cell indices)``.
UNITS = tuple(_build_units())


def _build_peers() -> Tuple[frozenset, ...]:
    peers = [set() for _ in range(CELL_COUNT)]
    for _, _, cells in UNITS:
        for i in cells:
            peers[i].update(cells)
    return tuple(frozenset(p - {i}) for i, p in enumerate(peers))


#: For each cell, the 20 other cells that share a row, column or box with it.
PEERS = _build_peers()


class Conflict(NamedTuple):
    """A digit that appears more than once inside a single unit."""

    unit: str
    number: int
    digit: int
    indices: Tuple[int, ...]

    def __str__(self) -> str:
        cells = ", ".join(cell_name(i) for i in self.indices)
        return f"digit {self.digit} repeats in {self.unit} {self.number} ({cells})"


class Board:
    """A mutable 9x9 Sudoku grid stored as a flat list; 0 means empty."""

    __slots__ = ("_cells",)

    def __init__(self, cells: Optional[Sequence[int]] = None) -> None:
        if cells is None:
            self._cells = [0] * CELL_COUNT
            return
        values = list(cells)
        if len(values) != CELL_COUNT:
            raise ParseError(f"expected {CELL_COUNT} cells, found {len(values)}")
        for v in values:
            if not isinstance(v, int) or not 0 <= v <= SIZE:
                raise ParseError(f"cell values must be integers 0-{SIZE}, got {v!r}")
        self._cells = values

    # ------------------------------------------------------------------ parsing
    @classmethod
    def from_string(cls, text: str) -> "Board":
        """Parse a grid written as digits, with 0 / '.' / '_' for empty cells.

        Whitespace and the separators ``| - +`` are ignored, so both the
        compact 81-character form and a pretty-printed grid are accepted.
        """
        cells: List[int] = []
        for ch in text:
            if ch.isspace() or ch in _IGNORED_CHARS:
                continue
            if ch in _BLANK_CHARS:
                cells.append(0)
            elif ch in "123456789":
                cells.append(int(ch))
            else:
                raise ParseError(f"unexpected character {ch!r}; use digits 1-9 and 0 or . for blanks")
        if len(cells) != CELL_COUNT:
            raise ParseError(f"expected {CELL_COUNT} cells, found {len(cells)}")
        return cls(cells)

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "Board":
        return cls.from_string(Path(path).read_text(encoding="utf-8"))

    # ------------------------------------------------------------------- access
    def __getitem__(self, index: int) -> int:
        return self._cells[index]

    def __setitem__(self, index: int, value: int) -> None:
        if not isinstance(value, int) or not 0 <= value <= SIZE:
            raise ValueError(f"value must be an integer 0-{SIZE}, got {value!r}")
        self._cells[index] = value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Board) and self._cells == other._cells

    __hash__ = None  # type: ignore[assignment]  # mutable, so unhashable

    def __repr__(self) -> str:
        return f"Board.from_string({self.to_line()!r})"

    def copy(self) -> "Board":
        return Board(self._cells)

    def to_list(self) -> List[int]:
        return list(self._cells)

    def empty_indices(self) -> List[int]:
        return [i for i, v in enumerate(self._cells) if v == 0]

    def clue_count(self) -> int:
        return CELL_COUNT - self._cells.count(0)

    # --------------------------------------------------------------- validation
    def is_complete(self) -> bool:
        return 0 not in self._cells

    def conflicts(self) -> List[Conflict]:
        """Every digit that repeats inside a row, column or box."""
        found: List[Conflict] = []
        for kind, number, cells in UNITS:
            seen = {}
            for i in cells:
                v = self._cells[i]
                if v:
                    seen.setdefault(v, []).append(i)
            for digit, where in sorted(seen.items()):
                if len(where) > 1:
                    found.append(Conflict(kind, number, digit, tuple(where)))
        return found

    def is_valid(self) -> bool:
        return not self.conflicts()

    def is_solved(self) -> bool:
        return self.is_complete() and self.is_valid()

    def validate(self) -> None:
        """Raise :class:`InvalidPuzzleError` if any unit has a repeated digit."""
        problems = self.conflicts()
        if problems:
            raise InvalidPuzzleError("; ".join(str(p) for p in problems))

    def candidates(self, index: int) -> Set[int]:
        """Digits that can legally go in a cell (empty set if already filled)."""
        if self._cells[index]:
            return set()
        return set(DIGITS) - {self._cells[p] for p in PEERS[index]}

    # --------------------------------------------------------------- formatting
    def to_line(self) -> str:
        """Compact 81-character form, '.' for empty cells."""
        return "".join(str(v) if v else "." for v in self._cells)

    def to_text(self) -> str:
        """Plain file format: nine lines of space-separated digits, 0 = empty."""
        rows = (self._cells[r * SIZE:(r + 1) * SIZE] for r in range(SIZE))
        return "\n".join(" ".join(str(v) for v in row) for row in rows) + "\n"

    def pretty(self, coordinates: bool = False) -> str:
        """Grid with box separators; optionally with 1-9 row/column labels."""
        rule = "+-------+-------+-------+"
        pad = "  " if coordinates else ""
        lines: List[str] = []
        if coordinates:
            lines.append("    1 2 3   4 5 6   7 8 9")
        lines.append(pad + rule)
        for r in range(SIZE):
            row = self._cells[r * SIZE:(r + 1) * SIZE]
            groups = (
                " ".join(str(v) if v else "." for v in row[b:b + BOX_SIZE])
                for b in range(0, SIZE, BOX_SIZE)
            )
            label = f"{r + 1} " if coordinates else ""
            lines.append(f"{label}| " + " | ".join(groups) + " |")
            if r % BOX_SIZE == BOX_SIZE - 1:
                lines.append(pad + rule)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.pretty()
