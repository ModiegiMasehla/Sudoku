# Sudoku

A Sudoku solver, puzzle generator and terminal game written in pure Python (no dependencies).

It started as a first-year coursework script that could only solve easy puzzles and sometimes
reported "solved" when it wasn't. This version is a ground-up rewrite with a proper package
layout, a complete solver, tests and CI.

## Features

- **Solve** any valid puzzle, including hard ones that need guessing
- **Explain** a solution step by step (naked singles and hidden singles)
- **Check** a puzzle: rule violations, no solution, one solution, or several
- **Generate** puzzles at three difficulties, each guaranteed to have exactly one solution
- **Play** in the terminal with hints, undo and mistake checking

## Install

Requires Python 3.9 or newer.

```bash
git clone <your-repo-url>
cd sudoku
pip install -e .
```

You can also run it without installing: `PYTHONPATH=src python -m sudoku ...`

## Usage

```bash
sudoku solve puzzles/hard.txt            # solve and print the grid
sudoku solve puzzles/first-year.txt --explain   # list every logical step
sudoku solve puzzle.txt -o solution.txt  # also save the solution
sudoku check puzzle.txt                  # validate and count solutions
sudoku generate -d hard --seed 7 -o new.txt
sudoku play                              # new medium puzzle
sudoku play -d easy                      # or choose a difficulty
sudoku play puzzles/first-year.txt       # or play a file
```

Puzzle files are nine lines of space-separated digits with `0` (or `.`) for empty cells.
Compact 81-character strings and pretty-printed grids are accepted too.

Example of `sudoku generate -d medium --seed 2024`:

```text
+-------+-------+-------+
| . . . | . . 4 | . 5 . |
| 2 9 7 | . . . | 3 8 . |
| . . . | . 2 . | . 1 9 |
+-------+-------+-------+
| 3 5 6 | . 7 1 | . . . |
| . 7 . | 2 5 . | . . . |
| 8 1 . | 9 3 . | 4 . . |
+-------+-------+-------+
| 5 2 . | . 1 . | 9 . . |
| 7 . 1 | . . 9 | 5 . . |
| . . 4 | . . . | . . . |
+-------+-------+-------+
```

Example of `sudoku solve puzzles/first-year.txt --explain`:

```text
  1. Naked single: R1C9 can only be 4, every other digit is already in its row, column or box
  2. Naked single: R1C4 can only be 3, every other digit is already in its row, column or box
  ...
```

### Playing

| Command | What it does |
| --- | --- |
| `3 4 7` | put 7 in row 3, column 4 |
| `clear 3 4` | erase a digit you placed |
| `undo` | take back your last move |
| `hint` | explain the next logical step (never fills a cell) |
| `check` | list cells that differ from the solution |
| `solve` | give up and show the solution |

## How it works

- **`board.py`**: the `Board` model. Parses several text formats, validates rules, computes
  candidates from precomputed peer tables, and formats grids.
- **`techniques.py`**: naked and hidden singles. Each returns a `Step` with a readable
  explanation, so the same code powers `--explain` and in-game hints.
- **`solver.py`**: depth-first search using one bitmask per row, column and box, always
  branching on the cell with the fewest candidates. It counts solutions up to a limit,
  which is how uniqueness is verified.
- **`generator.py`**: fills a random full grid, then removes cells in random order, keeping
  a removal only if the puzzle still has exactly one solution.
- **`game.py` / `play.py`**: game state and rules with no I/O, and a thin terminal loop on
  top, so whole games can be tested with scripted input.
- **`cli.py`**: `argparse` front end with clear errors and exit codes.



## Development

```bash
pip install -e ".[dev]"
python -m pytest
```
