import threading
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
        self.lock = threading.Lock()

    def push(self, data: str):
        with self.lock:
            if self.maxcols == 0:
                return

            attr = 0
            for rule, a in self.rules.items():
                if rule.matches(data):
                    attr = a
                    break

            for line in data.splitlines(keepends=False):
                while len(line) > 0:
                    b, line = line[: self.maxcols], line[self.maxcols :]
                    self.buf.append((b, attr))

    def resize(
        self,
        *,
        maxcols: int | None = None,
        maxrows: int | None = None,
    ):
        with self.lock:
            if maxcols is not None:
                self.maxcols = maxcols
            if maxrows is not None:
                self.maxrows = maxrows

            buf: deque[tuple[str, int]] = deque(maxlen=maxrows)
            for line in self.buf:
                buf.append((line[0][: self.maxcols], line[1]))
            self.buf = buf

    def __iter__(self) -> Generator[tuple[str, int], None, None]:
        with self.lock:
            yield from self.buf
