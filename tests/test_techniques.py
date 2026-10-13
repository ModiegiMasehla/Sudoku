from pathlib import Path

from sudoku.board import Board, index_of
from sudoku.techniques import (
    HIDDEN_SINGLE,
    NAKED_SINGLE,
    apply_logic,
    find_hidden_single,
    find_naked_single,
    next_step,
)

PUZZLES = Path(__file__).resolve().parent.parent / "puzzles"


def test_naked_single_is_found_and_explained():
    board = Board()
    for col, digit in enumerate(range(1, 9)):  # row 1 holds 1..8, so R1C9 must be 9
        board[index_of(0, col)] = digit
    step = find_naked_single(board)
    assert step is not None
    assert (step.technique, step.index, step.value) == (NAKED_SINGLE, index_of(0, 8), 9)
    assert "R1C9" in step.reason


def test_hidden_single_in_a_row():
    # Place a 1 below row 1 in every column except column 9, so within
    # row 1 the digit 1 has exactly one possible home: R1C9.
    board = Board()
    for row, col in [(1, 0), (2, 3), (3, 5), (4, 1), (5, 2), (6, 4), (7, 6), (8, 7)]:
        board[index_of(row, col)] = 1
    step = find_hidden_single(board)
    assert step is not None
    assert step.technique == HIDDEN_SINGLE
    assert (step.index, step.value) == (index_of(0, 8), 1)


def test_no_step_on_empty_board():
    assert next_step(Board()) is None


def test_no_step_when_a_cell_has_no_candidates():
    board = Board()
    for col in range(8):
        board[index_of(0, col)] = col + 1
    board[index_of(1, 8)] = 9  # R1C9 now has no legal digit
    assert next_step(board) is None


def test_logic_solves_the_first_year_puzzle_completely():
    board = Board.from_file(PUZZLES / "first-year.txt")
    steps = apply_logic(board)
    assert board.is_solved()
    assert len(steps) == 43
    assert {s.technique for s in steps} <= {NAKED_SINGLE, HIDDEN_SINGLE}


def test_logic_stalls_on_hard_puzzle_without_corrupting_it():
    board = Board.from_file(PUZZLES / "hard.txt")
    apply_logic(board)
    assert not board.is_complete()
    assert board.is_valid()


def test_every_step_is_legal_when_applied():
    board = Board.from_file(PUZZLES / "first-year.txt")
    while (step := next_step(board)) is not None:
        assert step.value in board.candidates(step.index)
        board[step.index] = step.value
        assert board.is_valid()
