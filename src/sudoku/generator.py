"""Puzzle generation: every puzzle has exactly one solution."""
from __future__ import annotations

import random
from typing import Dict, Optional

from .board import CELL_COUNT, Board
from .solver import count_solutions, random_solution

#: Clues left in the grid. Fewer clues generally means a harder puzzle.
DIFFICULTIES: Dict[str, int] = {"easy": 40, "medium": 32, "hard": 26}


def generate_puzzle(difficulty: str = "medium", seed: Optional[int] = None) -> Board:
    """Create a puzzle with a unique solution.

    Starts from a random full grid and removes cells in random order, keeping
    a removal only if the puzzle still has exactly one solution. The same
    ``seed`` always gives the same puzzle.
    """
    try:
        target_clues = DIFFICULTIES[difficulty]
    except KeyError:
        choices = ", ".join(DIFFICULTIES)
        raise ValueError(f"unknown difficulty {difficulty!r}; choose from {choices}") from None

    rng = random.Random(seed)
    puzzle = random_solution(rng)
    order = list(range(CELL_COUNT))
    rng.shuffle(order)

    clues = CELL_COUNT
    for index in order:
        if clues <= target_clues:
            break
        removed = puzzle[index]
        puzzle[index] = 0
        if count_solutions(puzzle, limit=2) == 1:
            clues -= 1
        else:
            puzzle[index] = removed
    return puzzle
