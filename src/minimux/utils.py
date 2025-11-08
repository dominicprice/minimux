import curses
import re
from typing import TypeVar

T = TypeVar("T")


def combine(t1: T, t2: T | None) -> T:
    "return t1 if t2 is None, else t2"
    if t2 is None:
        return t1
    return t2


def char_eq(a: int, b: int) -> bool:
    "returns True if a and b are equal characters, ignoring attributes"
    return (a & curses.A_CHARTEXT) == (b & curses.A_CHARTEXT)


ansi_re = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(s: str) -> str:
    "returns s with all ansi escape sequences removed"
    return ansi_re.sub("", s)
