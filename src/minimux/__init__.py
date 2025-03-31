import threading
import curses

from minimux.colour import ColourManager
from minimux.runner import Runner
from minimux.config import Config, Element, Panel, Command


class MiniMux:
    def __init__(
        self,
        config: Config,
    ):
        self.cm = ColourManager()
        self.config = config
        self.lock = threading.Lock()

    def run(self):
        """The main entrypoint"""
        curses.wrapper(self._run)

    def _run(self, stdscr: "curses._CursesWindow"):
        curses.use_default_colors()
        rows, cols = stdscr.getmaxyx()
        stdscr.clear()

        # Title
        start_row = 0
        if self.config.title:
            stdscr.move(0, 0)
            stdscr.addstr(
                self.config.title.center(cols),
                self.config.title_attr(self.cm),
            )
            self.hsep(stdscr, 1, 0, cols)
            start_row = 2

        # Content
        runners = self.init_content(
            stdscr,
            self.config.content,
            (start_row, rows),
            (0, cols),
        )

        # Ensure content drawn to stdscr is drawn
        stdscr.refresh()

        # start a thread for each runner
        threads = [
            threading.Thread(
                target=r.run,
                daemon=True,
            )
            for r in runners
        ]
        for thread in threads:
            thread.start()

        try:
            # wait for all runners to exit
            for thread in threads:
                thread.join()
            # keep open but ignore any keypresses
            while True:
                stdscr.getch()
        except KeyboardInterrupt:
            # keyboard interrupts are a normal way to exit
            pass
        finally:
            # kill all runners and wait for them to terminate
            # before exiting curses mode to avoid leaving the
            # terminal in a bad state
            wait_fns = [runner.terminate() for runner in runners]
            stdscr.clear()
            stdscr.move(rows // 2, 0)
            stdscr.addstr("Terminating...".center(cols))
            stdscr.refresh()
            for wait_fn in wait_fns:
                wait_fn()

    def init_content(
        self,
        stdscr: "curses._CursesWindow",
        content: Element,
        range_y: tuple[int, int],
        range_x: tuple[int, int],
    ) -> list[Runner]:
        """Recursively draw the static components for content and
        return the associated runners for any commands"""
        if isinstance(content, Panel):
            return self.init_panel(stdscr, content, range_y, range_x)
        elif isinstance(content, Command):
            return [self.init_command(stdscr, content, range_y, range_x)]
        else:
            raise TypeError

    def init_panel(
        self,
        stdscr: "curses._CursesWindow",
        panel: Panel,
        range_y: tuple[int, int],
        range_x: tuple[int, int],
    ) -> list[Runner]:
        """Recursively draw the static components for a panel and
        return the associated runners from any commands"""
        if len(panel.children) == 0:
            return []

        if panel.split_vertically:
            o = range_y[0]
            subh = (range_y[1] - range_y[0]) // sum(c.weight for c in panel.children)
            res: list[Runner] = []
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
                res += self.init_content(stdscr, child, subrange_y, range_x)
        else:
            i = 0
            o = range_x[0]
            subw = (range_x[1] - range_x[0]) // sum(c.weight for c in panel.children)
            res: list[Runner] = []
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
                res += self.init_content(stdscr, child, subrange_y, subrange_x)
                i += child.weight

        return res

    def init_command(
        self,
        stdscr: "curses._CursesWindow",
        command: Command,
        range_y: tuple[int, int],
        range_x: tuple[int, int],
    ) -> Runner:
        """Draw the static components for a command and return the
        associated runner"""
        if command.title is not None:
            stdscr.move(range_y[0], range_x[0])
            stdscr.addstr(
                command.title.center(range_x[1] - range_x[0]), command.attr(self.cm)
            )
            range_y = (range_y[0] + 1, range_y[1])
        win = stdscr.subwin(
            range_y[1] - range_y[0],
            range_x[1] - range_x[0],
            range_y[0],
            range_x[0],
        )
        win.bkgd(command.attr(self.cm))
        return Runner(command, self.lock, self.cm, win)

    def hsep(self, stdscr: "curses._CursesWindow", y: int, x: int, n: int):
        """Draw a horizontal seperator line, combining with existing
        separators to form tees and crosses"""
        attr = self.config.sep_attr(self.cm)
        if x > 0 and stdscr.inch(y, x - 1) == curses.ACS_SBSB:
            x -= 1
            n += 1
        for i in range(n):
            stdscr.move(y, x + i)
            cross = stdscr.inch(y, x + i) == curses.ACS_SBSB
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
        if y > 0 and stdscr.inch(y - 1, x) == curses.ACS_BSBS:
            y -= 1
            n += 1
        for i in range(n):
            cross = stdscr.inch(y + i, x) == curses.ACS_BSBS
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
