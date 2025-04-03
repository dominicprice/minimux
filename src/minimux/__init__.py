import curses
import threading

import minimux.utils as utils
from minimux.colour import ColourManager
from minimux.config import Command, Config, Element, Panel
from minimux.runner import Runner

__version__ = "1.3.0"
__version_info__ = (1, 3, 0)
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

    def _run(self, stdscr: "curses._CursesWindow"):
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

    def init(self, stdscr: "curses._CursesWindow"):
        rows, cols = stdscr.getmaxyx()
        stdscr.clear()

        start_row = 0
        if self.config.title:
            stdscr.move(0, 0)
            stdscr.addstr(
                self.config.title.center(cols),
                self.config.title_attr(self.cm),
            )
            self.hsep(stdscr, 1, 0, cols)
            start_row = 2

        self.init_content(
            stdscr,
            self.config.content,
            (start_row, rows),
            (0, cols),
        )
        stdscr.refresh()

    def init_content(
        self,
        stdscr: "curses._CursesWindow",
        content: Element,
        range_y: tuple[int, int],
        range_x: tuple[int, int],
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
        stdscr: "curses._CursesWindow",
        panel: Panel,
        range_y: tuple[int, int],
        range_x: tuple[int, int],
    ):
        """Recursively draw the static components for a panel and
        initialise the runners from any commands"""
        if len(panel.children) == 0:
            return []

        if panel.vertical:
            o = range_y[0]
            subh = (range_y[1] - range_y[0]) // sum(c.weight for c in panel.children)
            i = 0
            for child in panel.children:
                subrange_y = (o + i * subh, o + (i + child.weight) * subh)
                if i == len(panel.children) - 1:
                    subrange_y = (subrange_y[0], range_y[1])
                if i != 0:
                    self.hsep(
                        stdscr,
                        subrange_y[0],
                        range_x[0],
                        range_x[1] - range_x[0],
                    )
                    subrange_y = (subrange_y[0] + 1, subrange_y[1])
                i += child.weight
                self.init_content(stdscr, child, subrange_y, range_x)
        else:
            i = 0
            o = range_x[0]
            subw = (range_x[1] - range_x[0]) // sum(c.weight for c in panel.children)
            for child in panel.children:
                subrange_x = (o + i * subw, o + (i + child.weight) * subw)
                subrange_y = range_y
                if i == len(panel.children) - 1:
                    subrange_x = (subrange_x[0], range_x[1])
                if i != 0:
                    self.vsep(
                        stdscr,
                        range_y[0],
                        subrange_x[0],
                        range_y[1] - range_y[0],
                    )
                    subrange_x = (subrange_x[0] + 1, subrange_x[1])
                self.init_content(stdscr, child, subrange_y, subrange_x)
                i += child.weight

    def init_command(
        self,
        stdscr: "curses._CursesWindow",
        command: Command,
        range_y: tuple[int, int],
        range_x: tuple[int, int],
    ):
        """Draw the static components for a command initialise the
        associated runner"""
        if command.title is not None:
            stdscr.move(range_y[0], range_x[0])
            stdscr.addstr(" " * (range_x[1] - range_x[0]), command.attr(self.cm))
            self.center(
                stdscr,
                command.title,
                range_y[0],
                range_x[0],
                range_x[1] - range_x[0],
                command.title_attr(self.cm),
            )
            range_y = (range_y[0] + 1, range_y[1])
        self.runners[command.name].init(
            stdscr,
            (
                range_y[1] - range_y[0],
                range_x[1] - range_x[0],
                range_y[0],
                range_x[0],
            ),
        )

    def center(
        self,
        win: "curses._CursesWindow",
        s: str,
        y: int,
        x: int,
        n: int,
        attr: int,
    ):
        pad_left = (n - len(s)) // 2
        win.move(y, x + pad_left)
        win.addstr(s, attr)

    def hsep(self, stdscr: "curses._CursesWindow", y: int, x: int, n: int):
        """Draw a horizontal seperator line, combining with existing
        separators to form tees and crosses"""
        attr = self.config.sep_attr(self.cm)
        if x > 0 and utils.compare_char(stdscr.inch(y, x - 1), curses.ACS_SBSB):
            x -= 1
            n += 1
        for i in range(n):
            stdscr.move(y, x + i)
            cross = utils.compare_char(stdscr.inch(y, x + i), curses.ACS_SBSB)
            if cross:
                if i == 0:
                    stdscr.addch(curses.ACS_SSSB, attr)
                elif i == n - 1:
                    stdscr.addch(curses.ACS_SBSS, attr)
                else:
                    stdscr.addch(curses.ACS_SSSS, attr)
            else:
                stdscr.addch(curses.ACS_BSBS, attr)
        stdscr.noutrefresh()

    def vsep(self, stdscr: "curses._CursesWindow", y: int, x: int, n: int):
        """Draw a vertical seperator line, combining with existing
        separators to form tees and crosses"""
        attr = self.config.sep_attr(self.cm)
        if y > 0 and utils.compare_char(stdscr.inch(y - 1, x), curses.ACS_BSBS):
            y -= 1
            n += 1
        for i in range(n):
            cross = utils.compare_char(stdscr.inch(y + i, x), curses.ACS_BSBS)
            stdscr.move(y + i, x)
            if cross:
                if i == 0:
                    stdscr.addch(curses.ACS_BSSS, attr)
                elif i == n - 1:
                    stdscr.addch(curses.ACS_SSBS, attr)
                else:
                    stdscr.addch(curses.ACS_SSSS, attr)
            else:
                stdscr.addch(curses.ACS_SBSB, attr)
        stdscr.noutrefresh()
