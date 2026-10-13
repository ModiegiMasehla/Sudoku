from pathlib import Path

import pytest

from sudoku.cli import EXIT_BAD_INPUT, EXIT_OK, EXIT_PUZZLE_PROBLEM, main

PUZZLES = Path(__file__).resolve().parent.parent / "puzzles"


def test_solve_prints_grid_and_writes_output(tmp_path, capsys):
    out = tmp_path / "solution.txt"
    code = main(["solve", str(PUZZLES / "first-year.txt"), "-o", str(out)])
    captured = capsys.readouterr()
    assert code == EXIT_OK
    assert "| 9 6 2 | 3 7 8 | 5 1 4 |" in captured.out
    assert "Solved using logic only" in captured.err
    assert out.read_text().splitlines()[0] == "9 6 2 3 7 8 5 1 4"
    assert "0" not in out.read_text()


def test_solve_hard_puzzle_reports_that_search_was_needed(capsys):
    assert main(["solve", str(PUZZLES / "hard.txt")]) == EXIT_OK
    assert "needed search" in capsys.readouterr().err


def test_explain_lists_numbered_steps(capsys):
    main(["solve", str(PUZZLES / "first-year.txt"), "--explain"])
    out = capsys.readouterr().out
    assert "  1. " in out
    assert "Naked single" in out or "Hidden single" in out


def test_check_accepts_unique_puzzle(capsys):
    assert main(["check", str(PUZZLES / "first-year.txt")]) == EXIT_OK
    assert "exactly one solution" in capsys.readouterr().out


def test_check_reports_conflicts(tmp_path, capsys):
    bad = tmp_path / "bad.txt"
    bad.write_text("5 5 " + "0 " * 79)
    assert main(["check", str(bad)]) == EXIT_PUZZLE_PROBLEM
    assert "digit 5 repeats in row 1" in capsys.readouterr().out


def test_check_flags_multiple_solutions(tmp_path, capsys):
    empty = tmp_path / "empty.txt"
    empty.write_text("0 " * 81)
    assert main(["check", str(empty)]) == EXIT_PUZZLE_PROBLEM
    assert "more than one solution" in capsys.readouterr().out


def test_solve_rejects_rule_breaking_puzzle(tmp_path, capsys):
    bad = tmp_path / "bad.txt"
    bad.write_text("5 5 " + "0 " * 79)
    assert main(["solve", str(bad)]) == EXIT_PUZZLE_PROBLEM
    assert "error:" in capsys.readouterr().err


def test_solve_reports_malformed_file_without_a_traceback(tmp_path, capsys):
    bad = tmp_path / "bad.txt"
    bad.write_text("1 2 x\n")
    assert main(["solve", str(bad)]) == EXIT_BAD_INPUT
    assert "unexpected character" in capsys.readouterr().err


def test_missing_file_is_a_clean_error(capsys):
    assert main(["solve", "does-not-exist.txt"]) == EXIT_BAD_INPUT
    assert "error:" in capsys.readouterr().err


def test_command_is_required():
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_generate_writes_a_puzzle_that_check_accepts(tmp_path, capsys):
    out = tmp_path / "new.txt"
    assert main(["generate", "-d", "hard", "--seed", "42", "-o", str(out)]) == EXIT_OK
    captured = capsys.readouterr()
    assert "26 clues" in captured.err
    assert main(["check", str(out)]) == EXIT_OK


def test_generate_is_reproducible_with_a_seed(capsys):
    main(["generate", "--seed", "9"])
    first = capsys.readouterr().out
    main(["generate", "--seed", "9"])
    assert capsys.readouterr().out == first


def test_generate_rejects_unknown_difficulty():
    with pytest.raises(SystemExit) as exc:
        main(["generate", "-d", "nightmare"])
    assert exc.value.code == 2


def test_play_runs_an_interactive_session(monkeypatch, capsys):
    answers = iter(["hint", "quit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    assert main(["play", str(PUZZLES / "first-year.txt")]) == EXIT_OK
    out = capsys.readouterr().out
    assert "Hint:" in out
    assert "Thanks for playing" in out


def test_play_generates_a_puzzle_when_no_file_is_given(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _prompt="": "quit")
    assert main(["play", "-d", "easy", "--seed", "1"]) == EXIT_OK
    assert "Thanks for playing" in capsys.readouterr().out


def test_play_refuses_a_puzzle_with_several_solutions(tmp_path, capsys):
    empty = tmp_path / "empty.txt"
    empty.write_text("0 " * 81)
    assert main(["play", str(empty)]) == EXIT_BAD_INPUT
    assert "exactly one solution" in capsys.readouterr().err
