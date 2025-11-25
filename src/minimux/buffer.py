import threading
from typing import Generator

import pyte
import pyte.modes
from pyte.screens import Char


BUFFER_MAX_SIZE = 10000


class Buffer:
    """
    Holds lines of output of a command. Only enough lines to fill the
    height of the output space (maxrows) are kept, and lines are split
    so that each line is at most maxcols in length
    """

    def __init__(
        self,
        maxcols: int,
        maxrows: int,
    ):
        self.lock = threading.Lock()
        self.buf: str = ""

        # virtual terminal
        self.screen = pyte.Screen(maxcols, maxrows)
        self.screen.mode.add(pyte.modes.LNM)
        self.stream = pyte.Stream()
        self.stream.attach(self.screen)

    def push(self, data: str):
        "appends data to the buffer"
        with self.lock:
            self.buf += data
            if len(self.buf) > BUFFER_MAX_SIZE:
                self.buf = self.buf[len(self.buf) - BUFFER_MAX_SIZE :]
            self.stream.feed(data)

    def resize(
        self,
        *,
        maxcols: int | None = None,
        maxrows: int | None = None,
    ):
        "resizes the buffer"
        with self.lock:
            self.screen.resize(maxrows, maxcols)
            self.screen.erase_in_display(2)
            self.screen.cursor_position(0, 0)
            self.stream.feed(self.buf)

    def lines(self) -> Generator[list[Char], None, None]:
        with self.lock:
            for row in range(self.screen.lines):
                bufline = self.screen.buffer[row]
                yield [bufline[col] for col in range(self.screen.columns)]
