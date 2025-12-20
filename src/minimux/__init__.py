import curses
import threading
from pathlib import Path

from minimux.colour import ColourManager
from minimux.config import Config
from minimux.range import Range, Range2d
from minimux.runner import Runner
from minimux.utils import char_eq

__version__ = "2.0.0"
__version_info__ = (2, 0, 0)
__author__ = "Dominic Price"


class MiniMux:
    def __init__(
        self,
        stdscr: "curses.window",
        config: Config,
        cwd: Path,
    ):
        self.stdscr = stdscr
        self.config = config
        self.lock = threading.Lock()
        self.cwd = cwd
        self.runners: dict[str, Runner] = {}
        self.colour_manager = ColourManager()

    def run(self):
        curses.curs_set(False)
        curses.use_default_colors()

        self.runners = self.get_runners(self.config.content)
        self.joins = [runner.start() for runner in self.runners.values()]
        self.create_windows()

        try:
            # handle user input
            while True:
                if self.stdscr.getch() == curses.KEY_RESIZE:
                    self.create_windows()
        except KeyboardInterrupt:
            # keyboard interrupts are a normal way to exit
            pass
        finally:
            # kill all runners and wait for them to terminate
            # before exiting curses mode to avoid leaving the
            # terminal in a bad state
            rows, cols = self.stdscr.getmaxyx()
            for runner in self.runners.values():
                runner.stop()
            self.stdscr.clear()
            self.stdscr.move(rows // 2, 0)
            self.stdscr.addstr("Terminating...".center(cols))
            self.stdscr.refresh()

            # join all threads, collecting errors
            errors = []
            for join in self.joins:
                if err := join():
                    errors.append(err)

            # print errors and exit with non-zero status code
            if len(errors) > 0:
                for err in errors:
                    print(err)
                exit(1)

    def get_runners(self, content: Config.Element) -> dict[str, Runner]:
        if isinstance(content, Config.Panel):
            res: dict[str, Runner] = {}
            for child in content.children:
                res.update(self.get_runners(child))
            return res
        elif isinstance(content, Config.Command):
            return {content.name: Runner(content, self.doupdate, self.colour_manager)}
        else:
            raise TypeError

    def doupdate(self):
        """
        Call curses.doupdate() protected by a mutex so that it is
        safe to call from multiple threads
        """
        with self.lock:
            curses.doupdate()

    def create_windows(self):
        rows, cols = self.stdscr.getmaxyx()
        self.stdscr.clear()

        start_row = 0
        if self.config.title:
            self.stdscr.move(0, 0)
            self.stdscr.addstr(
                self.config.title.center(cols),
                self.config.title_attr(self.colour_manager),
            )
            self.hsep(1, Range(0, cols))
            start_row = 2

        self.init_content(
            self.config.content,
            Range(start_row, rows),
            Range(0, cols),
        )
        self.stdscr.refresh()

    def init_content(
        self,
        content: Config.Element,
        range_y: Range,
        range_x: Range,
    ):
        """Recursively draw the static components for content and
        initialise the runners for any commands"""
        if isinstance(content, Config.Panel):
            self.init_panel(content, range_y, range_x)
        elif isinstance(content, Config.Command):
            self.init_command(content, range_y, range_x)
        else:
            raise TypeError

    def init_panel(
        self,
        panel: Config.Panel,
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
                subrange_y = Range.offset(i * subh, (i + child.weight) * subh, o)
                if i == len(panel.children) - 1:
                    subrange_y = Range(subrange_y.start, range_y.end)
                if i != 0:
                    self.hsep(subrange_y.start, range_x)
                    subrange_y = subrange_y.trim(top=1)
                i += child.weight
                self.init_content(child, subrange_y, range_x)
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
                    self.vsep(subrange_x.start, range_y)
                    subrange_x = subrange_x.trim(top=1)
                self.init_content(child, subrange_y, subrange_x)
                i += child.weight

    def init_command(
        self,
        command: Config.Command,
        range_y: Range,
        range_x: Range,
    ):
        """Draw the static components for a command initialise the
        associated runner"""
        if command.title is not None:
            self.stdscr.move(range_y.start, range_x.start)
            self.stdscr.addstr(
                " " * (range_x.length),
                command.attr(self.colour_manager),
            )
            self.center(
                command.title,
                range_y.start,
                range_x,
                command.title_attr(self.colour_manager),
            )
            range_y = range_y.trim(top=1)
        self.runners[command.name].init(self.stdscr, Range2d(range_y, range_x))

    def center(self, s: str, y: int, x_range: Range, attr: int):
        pad_left = (x_range.length - len(s)) // 2
        self.stdscr.move(y, x_range.start + pad_left)
        self.stdscr.addstr(s, attr)

    def hsep(self, y: int, x_range: Range):
        """Draw a horizontal seperator line, combining with existing
        separators to form tees and crosses"""
        attr = self.config.sep_attr(self.colour_manager)
        _, max_x = self.stdscr.getmaxyx()
        if x_range.start > 0:
            if char_eq(self.stdscr.inch(y, x_range.start - 1), curses.ACS_SBSB):
                self.stdscr.move(y, x_range.start - 1)
                self.stdscr.addch(curses.ACS_SBSB, attr)
        if x_range.end <= max_x:
            if char_eq(self.stdscr.inch(y, x_range.end), curses.ACS_SBSB):
                self.stdscr.move(y, x_range.end)
                self.stdscr.addch(curses.ACS_SBSB, attr)
        for i in x_range.values():
            self.stdscr.move(y, i)
            self.stdscr.addch(curses.ACS_BSBS, attr)
        self.stdscr.noutrefresh()

    def vsep(self, x: int, y_range: Range):
        """Draw a vertical seperator line, combining with existing
        separators to form tees and crosses"""
        attr = self.config.sep_attr(self.colour_manager)
        max_y, _ = self.stdscr.getmaxyx()
        if y_range.start > 0:
            if char_eq(self.stdscr.inch(y_range.start - 1, x), curses.ACS_BSBS):
                self.stdscr.move(y_range.start - 1, x)
                self.stdscr.addch(curses.ACS_BSSS, attr)
        if y_range.end < max_y:
            if char_eq(self.stdscr.inch(y_range.end, x), curses.ACS_BSBS):
                self.stdscr.move(y_range.end, x)
                self.stdscr.addch(curses.ACS_BSSS, attr)
        for i in y_range.values():
            self.stdscr.move(i, x)
            self.stdscr.addch(curses.ACS_SBSB, attr)
        self.stdscr.noutrefresh()
