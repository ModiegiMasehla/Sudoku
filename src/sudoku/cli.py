"""Command-line interface: ``sudoku solve|check|generate|play``."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .board import Board, InvalidPuzzleError, ParseError, SudokuError
from .game import Game
from .generator import DIFFICULTIES, generate_puzzle
from .play import run as run_game
from .solver import UnsolvableError, count_solutions, solve

EXIT_OK = 0
EXIT_PUZZLE_PROBLEM = 1
EXIT_BAD_INPUT = 2


def _err(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)


def _load(path: str) -> Board:
    return Board.from_file(path)


def cmd_solve(args: argparse.Namespace) -> int:
    puzzle = _load(args.file)
    result = solve(puzzle)

    if args.explain:
        for number, step in enumerate(result.steps, start=1):
            print(f"{number:>3}. {step}")
        if result.steps:
            print()
    print(result.solution.pretty())

    if result.solved_by_logic:
        print(f"Solved using logic only ({len(result.steps)} steps).", file=sys.stderr)
    else:
        print(
            f"Logic found {len(result.steps)} steps; the rest needed search "
            f"({result.guesses} guesses).",
            file=sys.stderr,
        )
    if not result.unique:
        print("warning: the puzzle has more than one solution.", file=sys.stderr)

    if args.output:
        Path(args.output).write_text(result.solution.to_text(), encoding="utf-8")
        print(f"Solution written to {args.output}", file=sys.stderr)
    return EXIT_OK


def cmd_check(args: argparse.Namespace) -> int:
    puzzle = _load(args.file)
    conflicts = puzzle.conflicts()
    if conflicts:
        print("Invalid puzzle:")
        for conflict in conflicts:
            print(f"  - {conflict}")
        return EXIT_PUZZLE_PROBLEM

    solutions = count_solutions(puzzle, limit=2)
    print(f"{puzzle.clue_count()} clues, {81 - puzzle.clue_count()} empty cells.")
    if solutions == 0:
        print("Valid so far, but the puzzle has no solution.")
        return EXIT_PUZZLE_PROBLEM
    if solutions > 1:
        print("The puzzle has more than one solution.")
        return EXIT_PUZZLE_PROBLEM
    print("Valid puzzle with exactly one solution.")
    return EXIT_OK


def cmd_generate(args: argparse.Namespace) -> int:
    puzzle = generate_puzzle(args.difficulty, seed=args.seed)
    print(puzzle.pretty())
    print(f"{args.difficulty.capitalize()} puzzle, {puzzle.clue_count()} clues, one solution.", file=sys.stderr)
    if args.output:
        Path(args.output).write_text(puzzle.to_text(), encoding="utf-8")
        print(f"Puzzle written to {args.output}", file=sys.stderr)
    return EXIT_OK


def cmd_play(args: argparse.Namespace) -> int:
    if args.file:
        puzzle = _load(args.file)
    else:
        puzzle = generate_puzzle(args.difficulty, seed=args.seed)
    run_game(Game(puzzle), read=input, write=print)
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sudoku",
        description="Solve, check and generate Sudoku puzzles.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="command")

    solve_p = sub.add_parser("solve", help="solve a puzzle file")
    solve_p.add_argument("file", help="puzzle file (9 lines of digits, 0 or . for blanks)")
    solve_p.add_argument("-o", "--output", help="also write the solution to this file")
    solve_p.add_argument("--explain", action="store_true", help="list each logical step")
    solve_p.set_defaults(func=cmd_solve)

    check_p = sub.add_parser("check", help="validate a puzzle and count its solutions")
    check_p.add_argument("file", help="puzzle file")
    check_p.set_defaults(func=cmd_check)

    def add_generation_options(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "-d", "--difficulty", choices=sorted(DIFFICULTIES, key=DIFFICULTIES.get, reverse=True),
            default="medium", help="how many clues to leave (default: medium)",
        )
        p.add_argument("--seed", type=int, help="make the puzzle reproducible")

    gen_p = sub.add_parser("generate", help="create a new puzzle with a unique solution")
    add_generation_options(gen_p)
    gen_p.add_argument("-o", "--output", help="also write the puzzle to this file")
    gen_p.set_defaults(func=cmd_generate)

    play_p = sub.add_parser("play", help="play a puzzle in the terminal")
    play_p.add_argument("file", nargs="?", help="puzzle file (default: generate a new puzzle)")
    add_generation_options(play_p)
    play_p.set_defaults(func=cmd_play)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (InvalidPuzzleError, UnsolvableError) as exc:
        _err(str(exc))
        return EXIT_PUZZLE_PROBLEM
    except (ParseError, OSError) as exc:
        _err(str(exc))
        return EXIT_BAD_INPUT
    except SudokuError as exc:  # any other package error
        _err(str(exc))
        return EXIT_BAD_INPUT
    except KeyboardInterrupt:
        return 130
