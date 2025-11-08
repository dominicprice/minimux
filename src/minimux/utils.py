import curses
from typing import TypeVar
import re

T = TypeVar("T")


def combine(t1: T, t2: T) -> T:
    if t2 is None:
        return t1
    return t2


def compare_char(a: int, b: int) -> bool:
    return (a & curses.A_CHARTEXT) == (b & curses.A_CHARTEXT)


ansi_re = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(s: str) -> str:
    "returns s with all ansi escape sequences removed"
    return ansi_re.sub("", s)
