import pytest

from sudoku.board import (
    Board,
    InvalidPuzzleError,
    ParseError,
    box_of,
    cell_name,
    index_of,
)

PUZZLE = """
9 6 2 0 7 8 5 0 0
1 0 5 0 0 9 3 0 0
3 0 0 0 0 0 8 2 0
0 0 1 0 0 0 0 7 0
6 0 0 0 5 0 0 0 8
0 0 0 6 0 3 9 0 5
0 1 8 0 0 5 0 0 0
0 0 6 8 3 2 7 0 1
7 5 3 1 9 0 4 8 0
"""


def test_parses_original_file_format():
    board = Board.from_string(PUZZLE)
    assert board[0] == 9
    assert board[3] == 0
    assert board.clue_count() == 38


def test_parses_compact_and_dotted_forms():
    line = "." * 80 + "5"
    assert Board.from_string(line)[80] == 5
    assert Board.from_string(line) == Board.from_string(line.replace(".", "0"))


def test_pretty_output_round_trips():
    board = Board.from_string(PUZZLE)
    assert Board.from_string(board.pretty()) == board
    assert Board.from_string(board.pretty(coordinates=False)) == board


def test_text_output_round_trips_and_matches_v1_format():
    board = Board.from_string(PUZZLE)
    assert board.to_text().splitlines()[0] == "9 6 2 0 7 8 5 0 0"
    assert Board.from_string(board.to_text()) == board


@pytest.mark.parametrize("bad", ["", "1 2 x", "1" * 80, "1" * 82, "10 " * 27])
def test_bad_input_raises_parse_error_instead_of_crashing(bad):
    with pytest.raises(ParseError):
        Board.from_string(bad)


def test_constructor_rejects_bad_values():
    with pytest.raises(ParseError):
        Board([0] * 80)
    with pytest.raises(ParseError):
        Board([10] + [0] * 80)


def test_setitem_rejects_out_of_range_digit():
    board = Board()
    with pytest.raises(ValueError):
        board[0] = 10


def test_detects_row_column_and_box_conflicts():
    board = Board()
    board[index_of(0, 0)] = 5
    board[index_of(0, 8)] = 5   # same row
    board[index_of(8, 0)] = 5   # same column
    board[index_of(1, 1)] = 5   # same box as (0, 0)
    kinds = {c.unit for c in board.conflicts()}
    assert kinds == {"row", "column", "box"}
    assert not board.is_valid()
    with pytest.raises(InvalidPuzzleError, match="digit 5 repeats in row 1"):
        board.validate()


def test_valid_partial_board_has_no_conflicts():
    board = Board.from_string(PUZZLE)
    assert board.is_valid()
    assert not board.is_complete()
    assert not board.is_solved()


def test_candidates_exclude_row_column_and_box_digits():
    board = Board.from_string(PUZZLE)
    assert board.candidates(index_of(0, 3)) == {3, 4}
    assert board.candidates(index_of(0, 0)) == set()  # already filled


def test_box_numbering_and_cell_names():
    assert box_of(index_of(0, 0)) == 0
    assert box_of(index_of(4, 4)) == 4
    assert box_of(index_of(8, 8)) == 8
    assert cell_name(index_of(2, 3)) == "R3C4"


def test_index_of_checks_bounds():
    with pytest.raises(IndexError):
        index_of(9, 0)


def test_pretty_has_box_separators_and_coordinates():
    text = Board.from_string(PUZZLE).pretty(coordinates=True)
    lines = text.splitlines()
    assert lines[0].strip() == "1 2 3   4 5 6   7 8 9"
    assert lines[2] == "1 | 9 6 2 | . 7 8 | 5 . . |"
    assert sum(1 for line in lines if line.strip().startswith("+")) == 4


def test_copy_is_independent():
    a = Board.from_string(PUZZLE)
    b = a.copy()
    b[3] = 3
    assert a[3] == 0 and b[3] == 3
