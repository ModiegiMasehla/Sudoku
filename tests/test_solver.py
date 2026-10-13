from pathlib import Path

import pytest

from sudoku.board import Board, InvalidPuzzleError
from sudoku.solver import UnsolvableError, count_solutions, random_solution, solve

PUZZLES = Path(__file__).resolve().parent.parent / "puzzles"

HARD_SOLUTION = (
    "812753649943682175675491283154237896369845721287169534521974368438526917796318452"
)
FIRST_YEAR_SOLUTION = (
    "962378514185429367374561829531984276649257138827613945218745693496832751753196482"
)


def test_solves_first_year_puzzle():
    result = solve(Board.from_file(PUZZLES / "first-year.txt"))
    assert result.solution.is_solved()
    assert result.solution.to_line() == FIRST_YEAR_SOLUTION
    assert result.unique
    assert result.solved_by_logic
    assert result.guesses == 0


def test_solves_hard_puzzle_that_v1_could_not():
    result = solve(Board.from_file(PUZZLES / "hard.txt"))
    assert result.solution.to_line() == HARD_SOLUTION
    assert result.unique
    assert not result.solved_by_logic
    assert result.guesses > 0


def test_solution_keeps_every_given():
    puzzle = Board.from_file(PUZZLES / "hard.txt")
    solution = solve(puzzle).solution
    assert all(solution[i] == puzzle[i] for i in range(81) if puzzle[i])


def test_input_board_is_not_modified():
    puzzle = Board.from_file(PUZZLES / "hard.txt")
    before = puzzle.to_line()
    solve(puzzle)
    assert puzzle.to_line() == before


def test_rule_breaking_puzzle_is_rejected():
    puzzle = Board.from_string("55" + "0" * 79)
    with pytest.raises(InvalidPuzzleError):
        solve(puzzle)


def test_valid_looking_but_unsolvable_puzzle_is_reported():
    # R1C1 has no legal digit: 1-8 sit in its row/column and 9 in its box.
    puzzle = Board()
    for col, digit in enumerate(range(1, 5), start=1):
        puzzle[col] = digit
    for row, digit in enumerate(range(5, 9), start=1):
        puzzle[row * 9] = digit
    puzzle[10] = 9
    assert puzzle.is_valid()
    with pytest.raises(UnsolvableError):
        solve(puzzle)
    assert count_solutions(puzzle) == 0


def test_empty_board_has_many_solutions_and_search_stops_at_limit():
    assert count_solutions(Board(), limit=2) == 2
    assert count_solutions(Board(), limit=5) == 5


def test_non_unique_puzzle_is_flagged():
    result = solve(Board())
    assert result.solution.is_solved()
    assert not result.unique


def test_already_solved_board_is_returned_as_is():
    solved = Board.from_string(HARD_SOLUTION)
    result = solve(solved)
    assert result.solution == solved
    assert result.steps == []
    assert result.unique


def test_count_solutions_of_invalid_board_is_zero():
    assert count_solutions(Board.from_string("55" + "0" * 79)) == 0


def test_random_solution_is_valid_and_seeded():
    import random

    a = random_solution(random.Random(7))
    b = random_solution(random.Random(7))
    c = random_solution(random.Random(8))
    assert a.is_solved()
    assert a == b
    assert a != c
