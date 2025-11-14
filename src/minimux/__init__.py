import curses
import threading

from minimux.utils import Range, WindowBounds, char_eq
from minimux.colour import ColourManager
from minimux.config import Command, Config, Element, Panel
from minimux.runner import Runner

__version__ = "1.4.0"
__version_info__ = (1, 4, 0)
__author__ = "Dominic Price"


class MiniMux:
    def __init__(
        self,
        config: Config,
    ):
        self.cm = ColourManager()
        self.config = config
        self.lock = threading.Lock()
        self.runners: dict[str, Runner] = {}

    def run(self):
        """The main entrypoint"""
        curses.wrapper(self._run)

    def _run(self, stdscr: "curses.window"):
        curses.curs_set(False)
        curses.use_default_colors()

        self.runners = self.get_runners(self.config.content)
        for runner in self.runners.values():
            runner.start()
        self.init(stdscr)

        try:
            # handle user input
            while True:
                if stdscr.getch() == curses.KEY_RESIZE:
                    self.init(stdscr)
        except KeyboardInterrupt:
            # keyboard interrupts are a normal way to exit
            pass
        finally:
            # kill all runners and wait for them to terminate
            # before exiting curses mode to avoid leaving the
            # terminal in a bad state
            rows, cols = stdscr.getmaxyx()
            wait_fns = [runner.terminate() for runner in self.runners.values()]
            stdscr.clear()
            stdscr.move(rows // 2, 0)
            stdscr.addstr("Terminating...".center(cols))
            stdscr.refresh()
            for wait_fn in wait_fns:
                wait_fn()

    def get_runners(self, content: Element) -> dict[str, Runner]:
        if isinstance(content, Panel):
            res: dict[str, Runner] = {}
            for child in content.children:
                res.update(self.get_runners(child))
            return res
        elif isinstance(content, Command):
            return {content.name: Runner(content, self.lock, self.cm)}
        else:
            raise TypeError

    def init(self, stdscr: "curses.window"):
        rows, cols = stdscr.getmaxyx()
        stdscr.clear()

        start_row = 0
        if self.config.title:
            stdscr.move(0, 0)
            stdscr.addstr(
                self.config.title.center(cols),
                self.config.title_attr(self.cm),
            )
            self.hsep(stdscr, 1, Range(0, cols))
            start_row = 2

        self.init_content(
            stdscr,
            self.config.content,
            Range(start_row, rows),
            Range(0, cols),
        )
        stdscr.refresh()

    def init_content(
        self,
        stdscr: "curses.window",
        content: Element,
        range_y: Range,
        range_x: Range,
    ):
        """Recursively draw the static components for content and
        initialise the runners for any commands"""
        if isinstance(content, Panel):
            self.init_panel(stdscr, content, range_y, range_x)
        elif isinstance(content, Command):
            self.init_command(stdscr, content, range_y, range_x)
        else:
            raise TypeError

    def init_panel(
        self,
        stdscr: "curses.window",
        panel: Panel,
        range_y: Range,
        range_x: Range,
    ):
        """Recursively draw the static components for a panel and
        initialise the runners from any commands"""
        if len(panel.children) == 0:
            return

        if panel.vertical:
            o = range_y.start
            subh = (range_y.length) // sum(c.weight for c in panel.children)
            i = 0
            for child in panel.children:
                subrange_y = Range.offset(i * subh, i + child.weight, o)
                if i == len(panel.children) - 1:
                    subrange_y = Range(subrange_y.start, range_y.end)
                if i != 0:
                    self.hsep(stdscr, subrange_y.start, range_x)
                    subrange_y = subrange_y.trim(top=1)
                i += child.weight
                self.init_content(stdscr, child, subrange_y, range_x)
        else:
            i = 0
            o = range_x.start
            subw = (range_x.length) // sum(c.weight for c in panel.children)
            for child in panel.children:
                subrange_x = Range.offset(i * subw, (i + child.weight) * subw, o)
                subrange_y = range_y
                if i == len(panel.children) - 1:
                    subrange_x = Range(subrange_x.start, range_x.end)
                if i != 0:
                    self.vsep(stdscr, subrange_x.start, range_y)
                    subrange_x = subrange_x.trim(top=1)
                self.init_content(stdscr, child, subrange_y, subrange_x)
                i += child.weight

    def init_command(
        self,
        stdscr: "curses.window",
        command: Command,
        range_y: Range,
        range_x: Range,
    ):
        """Draw the static components for a command initialise the
        associated runner"""
        if command.title is not None:
            stdscr.move(range_y.start, range_x.start)
            stdscr.addstr(" " * (range_x.length), command.attr(self.cm))
            self.center(
                stdscr,
                command.title,
                range_y.start,
                range_x,
                command.title_attr(self.cm),
            )
            range_y = range_y.trim(top=1)
        self.runners[command.name].init(
            stdscr,
            WindowBounds.from_ranges(range_y, range_x),
        )

    def center(
        self,
        win: "curses.window",
        s: str,
        y: int,
        x_range: Range,
        attr: int,
    ):
        pad_left = (x_range.length - len(s)) // 2
        win.move(y, x_range.start + pad_left)
        win.addstr(s, attr)

    def hsep(self, stdscr: "curses.window", y: int, x_range: Range):
        """Draw a horizontal seperator line, combining with existing
        separators to form tees and crosses"""
        attr = self.config.sep_attr(self.cm)
        if x_range.start > 0:
            if char_eq(stdscr.inch(y, x_range.end - 1), curses.ACS_SBSB):
                x_range = x_range.trim(top=-1, tail=1)
        for i in x_range.values():
            stdscr.move(y, i)
            cross = char_eq(stdscr.inch(y, i), curses.ACS_SBSB)
            if cross:
                if i == x_range.start:
                    stdscr.addch(curses.ACS_SSSB, attr)
                elif i == x_range.end - 1:
                    stdscr.addch(curses.ACS_SBSS, attr)
                else:
                    stdscr.addch(curses.ACS_SSSS, attr)
            else:
                stdscr.addch(curses.ACS_BSBS, attr)
        stdscr.noutrefresh()

    def vsep(self, stdscr: "curses.window", x: int, y_range: Range):
        """Draw a vertical seperator line, combining with existing
        separators to form tees and crosses"""
        attr = self.config.sep_attr(self.cm)
        if y_range.start > 0:
            if char_eq(stdscr.inch(y_range.start - 1, x), curses.ACS_BSBS):
                y_range = y_range.trim(top=-1, tail=1)
        for i in y_range.values():
            cross = char_eq(stdscr.inch(i, x), curses.ACS_BSBS)
            stdscr.move(i, x)
            if cross:
                if i == y_range.start:
                    stdscr.addch(curses.ACS_BSSS, attr)
                elif i == y_range.end - 1:
                    stdscr.addch(curses.ACS_SSBS, attr)
                else:
                    stdscr.addch(curses.ACS_SSSS, attr)
            else:
                stdscr.addch(curses.ACS_SBSB, attr)
        stdscr.noutrefresh()
