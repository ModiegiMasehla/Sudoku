import pytest

from sudoku.generator import DIFFICULTIES, generate_puzzle
from sudoku.solver import count_solutions, solve


@pytest.mark.parametrize("difficulty", sorted(DIFFICULTIES))
def test_generated_puzzles_are_valid_and_unique(difficulty):
    puzzle = generate_puzzle(difficulty, seed=123)
    assert puzzle.is_valid()
    assert not puzzle.is_complete()
    assert count_solutions(puzzle, limit=2) == 1
    assert solve(puzzle).solution.is_solved()


def test_clue_count_matches_the_difficulty_target():
    easy = generate_puzzle("easy", seed=1)
    hard = generate_puzzle("hard", seed=1)
    assert easy.clue_count() == DIFFICULTIES["easy"]
    assert hard.clue_count() <= DIFFICULTIES["easy"]
    assert hard.clue_count() < easy.clue_count()


def test_same_seed_gives_same_puzzle_and_different_seed_differs():
    assert generate_puzzle("medium", seed=5) == generate_puzzle("medium", seed=5)
    assert generate_puzzle("medium", seed=5) != generate_puzzle("medium", seed=6)


def test_unknown_difficulty_is_rejected():
    with pytest.raises(ValueError, match="unknown difficulty"):
        generate_puzzle("impossible")


@pytest.mark.parametrize("seed", range(15))
def test_generate_then_solve_end_to_end(seed):
    difficulty = sorted(DIFFICULTIES)[seed % len(DIFFICULTIES)]
    puzzle = generate_puzzle(difficulty, seed=seed)
    result = solve(puzzle)
    assert result.unique
    assert result.solution.is_solved()
    assert all(result.solution[i] == puzzle[i] for i in range(81) if puzzle[i])
