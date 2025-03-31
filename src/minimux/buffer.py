from collections import deque
from typing import Generator

from minimux.rules import Rule


class Buffer:
    def __init__(
        self,
        maxcols: int,
        maxrows: int,
        rules: dict[Rule, int] | None = None,
    ):
        self.buf: deque[tuple[str, int]] = deque(maxlen=maxrows)
        self.maxcols = maxcols
        self.rules = rules if rules is not None else {}

    def push(self, data: str):
        attr = 0
        for rule, a in self.rules.items():
            if rule.matches(data):
                attr = a
                break

        for line in data.splitlines(keepends=False):
            while len(line) > 0:
                b, line = line[: self.maxcols], line[self.maxcols :]
                self.buf.append((b, attr))

    def __iter__(self) -> Generator[tuple[str, int], None, None]:
        yield from self.buf
