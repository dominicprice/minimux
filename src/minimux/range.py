from typing import Generator, NamedTuple


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


class Range2d(NamedTuple):
    rows: Range
    cols: Range
