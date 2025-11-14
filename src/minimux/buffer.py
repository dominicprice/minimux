from dataclasses import dataclass
import threading
from typing import Generator
import pyte
import pyte.modes

from minimux.colour import ColourManager
from minimux.config import Attr
from minimux.utils import debug


@dataclass
class RichText:
    text: str
    attr: int


@dataclass
class OutputLine:
    elements: list[RichText]


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
        colour_manager: ColourManager,
    ):
        self.colour_manager = colour_manager
        self.lock = threading.Lock()

        # virtual terminal
        self.screen = pyte.Screen(maxcols, maxrows)
        self.screen.mode.add(pyte.modes.LNM)
        self.stream = pyte.Stream()
        self.stream.attach(self.screen)

    def push(self, data: str):
        "appends data to the buffer"
        debug("sending", data, name="buffer")
        with self.lock:
            self.stream.feed(data)

    def resize(
        self,
        *,
        maxcols: int | None = None,
        maxrows: int | None = None,
    ):
        "resizes the buffer"
        debug("buffer", "resizing to", maxcols, maxrows)
        with self.lock:
            self.screen.resize(maxrows, maxcols)

    def __iter__(self) -> Generator[OutputLine, None, None]:
        with self.lock:
            for row in range(self.screen.lines):
                bufline = self.screen.buffer[row]
                prev_attr = -1
                line = OutputLine([])
                for col in range(self.screen.columns):
                    char = bufline[col]
                    attr = Attr.from_char(char)(self.colour_manager)
                    if attr != prev_attr:
                        rt = RichText(char.data, attr)
                        line.elements.append(rt)
                        prev_attr = attr
                    else:
                        line.elements[len(line.elements) - 1].text += char.data
                yield line
