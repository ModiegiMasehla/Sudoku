"""Interactive terminal front end for :class:`~sudoku.game.Game`."""
from __future__ import annotations

from typing import Callable

from .board import cell_name
from .game import Game, MoveError

HELP = """\
Commands:
  <row> <col> <digit>   place a digit, e.g. "3 4 7" puts 7 in row 3, column 4
  clear <row> <col>     erase a digit you placed
  undo                  take back your last move
  hint                  get a hint (it never fills a cell for you)
  check                 show cells that differ from the solution
  solve                 give up and reveal the solution
  help                  show this message
  quit                  leave the game
"""


def run(
    game: Game,
    read: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
) -> bool:
    """Play until the puzzle is solved or the player quits.

    Returns True if the player solved it themselves. ``read`` and ``write``
    can be replaced, which is how the tests drive a whole game.
    """
    write("Sudoku: fill every row, column and 3x3 box with the digits 1-9.")
    write(HELP)
    while True:
        write(game.board.pretty(coordinates=True))
        try:
            line = read("> ").strip().lower()
        except EOFError:
            write("")
            return False
        if not line:
            continue
        parts = line.split()
        command = parts[0]

        try:
            if command in ("quit", "exit", "q"):
                write("Thanks for playing.")
                return False
            if command in ("help", "?"):
                write(HELP)
            elif command == "undo":
                write(f"Undone: {game.undo()}")
            elif command == "hint":
                write(f"Hint: {game.hint()}")
            elif command == "check":
                wrong = game.wrong_cells()
                if wrong:
                    names = ", ".join(cell_name(i) for i in wrong)
                    write(f"Incorrect: {names}")
                else:
                    write("So far so good, no mistakes.")
            elif command == "solve":
                write("Solution:")
                write(game.solution.pretty(coordinates=True))
                return False
            elif command == "clear" and len(parts) == 3:
                game.clear(int(parts[1]), int(parts[2]))
            elif len(parts) == 3 and all(p.isdigit() for p in parts):
                clashes = game.place(*(int(p) for p in parts))
                if clashes:
                    names = ", ".join(cell_name(i) for i in clashes)
                    write(f"Careful: that digit already appears in {names}.")
            else:
                write("Unknown command, type 'help' for the list.")
                continue
        except MoveError as exc:
            write(f"Not allowed: {exc}")
            continue
        except ValueError:
            write("Rows, columns and digits must be whole numbers.")
            continue

        if game.is_won():
            write(game.board.pretty(coordinates=True))
            write(f"Solved in {game.moves} moves with {game.hints_used} hints. Well done!")
            return True
