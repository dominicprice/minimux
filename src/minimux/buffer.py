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
        tabsize: int,
    ):
        self.buf: str = ""
        self.tabsize = tabsize

        # virtual terminal
        self.screen = pyte.Screen(maxcols, maxrows)
        self.stream = pyte.Stream()
        self.stream.attach(self.screen)
        self.reset()

    @property
    def rows(self) -> int:
        return self.screen.lines

    @property
    def cols(self) -> int:
        return self.screen.columns

    def push(self, data: str):
        "appends data to the buffer"
        self.buf += data
        if len(self.buf) > BUFFER_MAX_SIZE:
            self.buf = self.buf[len(self.buf) - BUFFER_MAX_SIZE :]
        self.stream.feed(data)

    def reset(self, clear_buffer: bool = True):
        "clears the buffer of all data"
        if clear_buffer:
            self.buf = ""
        self.screen.reset()
        self.screen.mode.add(pyte.modes.LNM)
        ntabs = self.screen.columns // self.tabsize
        self.screen.tabstops = set(i * self.tabsize for i in range(ntabs))

    def resize(
        self,
        *,
        maxcols: int | None = None,
        maxrows: int | None = None,
    ):
        "resizes the buffer"
        self.screen.resize(maxrows, maxcols)
        self.reset(False)
        self.stream.feed(self.buf)

    def lines(self) -> Generator[list[Char], None, None]:
        for row in range(self.screen.lines):
            bufline = self.screen.buffer[row]
            yield [bufline[col] for col in range(self.screen.columns)]
