from pathlib import Path

import pytest

from sudoku.board import Board, SudokuError, index_of
from sudoku.game import Game, MoveError
from sudoku.play import run

PUZZLES = Path(__file__).resolve().parent.parent / "puzzles"


@pytest.fixture
def game():
    return Game(Board.from_file(PUZZLES / "first-year.txt"))


def missing_cell(game):
    """First empty cell as (row, col, correct digit), one-based."""
    index = game.board.empty_indices()[0]
    return index // 9 + 1, index % 9 + 1, game.solution[index]


def test_game_rejects_puzzles_without_a_unique_solution():
    with pytest.raises(SudokuError):
        Game(Board())


def test_placing_a_correct_digit_has_no_clashes(game):
    row, col, digit = missing_cell(game)
    assert game.place(row, col, digit) == []
    assert game.board[index_of(row - 1, col - 1)] == digit
    assert game.wrong_cells() == []


def test_clashing_digit_is_placed_but_reported(game):
    row, col, digit = missing_cell(game)
    legal = game.board.candidates(index_of(row - 1, col - 1))
    wrong = next(d for d in range(1, 10) if d not in legal)  # clashes with a peer
    assert game.place(row, col, wrong)  # non-empty list of clashing peers
    assert game.wrong_cells() == [index_of(row - 1, col - 1)]


def test_givens_cannot_be_changed_or_cleared(game):
    with pytest.raises(MoveError, match="cannot be changed"):
        game.place(1, 1, 5)
    with pytest.raises(MoveError, match="cannot be changed"):
        game.clear(1, 1)


@pytest.mark.parametrize("args", [(0, 1, 1), (1, 10, 1), (1, 1, 0), (1, 4, 10)])
def test_out_of_range_moves_are_rejected(game, args):
    with pytest.raises(MoveError):
        game.place(*args)


def test_undo_restores_previous_state(game):
    row, col, digit = missing_cell(game)
    game.place(row, col, digit)
    game.undo()
    assert game.board[index_of(row - 1, col - 1)] == 0
    with pytest.raises(MoveError, match="nothing to undo"):
        game.undo()


def test_clear_and_undo_round_trip(game):
    row, col, digit = missing_cell(game)
    game.place(row, col, digit)
    game.clear(row, col)
    assert game.board[index_of(row - 1, col - 1)] == 0
    game.undo()
    assert game.board[index_of(row - 1, col - 1)] == digit


def test_hint_explains_a_deduction_without_filling_the_cell(game):
    before = game.board.to_line()
    hint = game.hint()
    assert game.board.to_line() == before
    assert game.hints_used == 1
    assert "R" in hint and "C" in hint


def test_hint_points_out_a_mistake_first(game):
    row, col, digit = missing_cell(game)
    wrong = 1 if digit != 1 else 2
    game.place(row, col, wrong)
    assert "looks wrong" in game.hint()


def test_hint_on_hard_puzzle_falls_back_to_the_solution():
    hard = Game(Board.from_file(PUZZLES / "hard.txt"))
    assert "Try R" in hard.hint()


def test_winning_is_detected(game):
    for index in game.board.empty_indices():
        game.place(index // 9 + 1, index % 9 + 1, game.solution[index])
    assert game.is_won()


def scripted(commands):
    feed = iter(commands)
    output = []

    def read(_prompt):
        try:
            return next(feed)
        except StopIteration:
            raise EOFError

    return read, output.append, output


def test_terminal_session_plays_to_a_win(game):
    moves = [
        f"{i // 9 + 1} {i % 9 + 1} {game.solution[i]}" for i in game.board.empty_indices()
    ]
    read, write, output = scripted(["help", "hint", *moves])
    assert run(game, read, write) is True
    assert any("Well done" in line for line in output)


def test_terminal_reports_bad_input_and_quits(game):
    read, write, output = scripted(["banana", "1 1 5", "9 9", "0 0 0", "quit"])
    assert run(game, read, write) is False
    text = "\n".join(output)
    assert "Unknown command" in text
    assert "cannot be changed" in text
    assert "Thanks for playing" in text


def test_terminal_stops_cleanly_on_end_of_input(game):
    read, write, _ = scripted([])
    assert run(game, read, write) is False


def test_terminal_check_and_solve_commands(game):
    read, write, output = scripted(["check", "solve"])
    assert run(game, read, write) is False
    text = "\n".join(output)
    assert "no mistakes" in text
    assert "Solution:" in text
