import curses
import re
from typing import Generator, NamedTuple, TypeVar
import threading

T = TypeVar("T")


class Range(NamedTuple):
    start: int
    end: int

    @classmethod
    def offset(cls, start: int, end: int, offset: int) -> "Range":
        return cls(start + offset, end + offset)

    @property
    def length(self) -> int:
        return self.end - self.start

    def trim(self, *, top: int = 0, tail: int = 0) -> "Range":
        return Range(self.start + top, self.end - tail)

    def values(self) -> Generator[int, None, None]:
        yield from range(self.start, self.end)


class WindowBounds(NamedTuple):
    rows: int
    cols: int
    start_row: int
    start_col: int

    @classmethod
    def from_ranges(cls, range_y: Range, range_x: Range) -> "WindowBounds":
        return cls(
            range_y.length,
            range_x.length,
            range_y.start,
            range_x.start,
        )


def combine(t1: T, t2: T | None) -> T:
    "return t1 if t2 is None, else t2"
    if t2 is None:
        return t1
    return t2


def char_eq(a: int, b: int) -> bool:
    "returns True if a and b are equal characters, ignoring attributes"
    return (a & curses.A_CHARTEXT) == (b & curses.A_CHARTEXT)


debug_file = open("debug.txt", "w")
debug_lock = threading.Lock()


def debug(*args, name: str | None = None):
    with debug_lock:
        debug_file.write("# " + (name or "debug") + "\n")
        print(*args, file=debug_file)
