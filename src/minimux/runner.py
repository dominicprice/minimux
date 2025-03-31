import threading
import subprocess
import curses
from typing import Any, Callable, TypeAlias


from minimux.buffer import Buffer
from minimux.colour import ColourManager
from minimux.config import Command

WindowBounds: TypeAlias = tuple[int, int, int, int]


class Runner:
    def __init__(
        self,
        command: Command,
        lock: threading.Lock,
        colour_manager: ColourManager,
    ):
        self.command = command
        self.lock = lock
        self.win: "curses._CursesWindow | None" = None
        self.proc: subprocess.Popen[str] | None = None
        self.bkgd = command.attr(colour_manager)

        self.buf = Buffer(
            0,
            0,
            {k: v(colour_manager) for k, v in command.rules.items()},
        )

    def init(self, stdscr: "curses._CursesWindow", bounds: WindowBounds):
        with self.lock:
            if self.win is not None:
                del self.win
            self.win = stdscr.subwin(*bounds)
            self.win.bkgdset(" ", self.bkgd)
            self.buf.resize(maxrows=bounds[0], maxcols=bounds[1])
        self.flush()

    def start(self):
        t = threading.Thread(target=self.run, daemon=True)
        t.start()

    def run(self):
        try:
            self.proc = subprocess.Popen(
                self.command.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
            )
        except Exception as e:
            self.buf.push("error: failed to start process: " + str(e))
            self.flush()
            return

        assert self.proc.stdout is not None

        while self.proc.poll() is None:
            stdout = self.proc.stdout.readline().rstrip()
            self.buf.push(stdout)
            self.flush()

        self.buf.push(f"Process exited with status code {self.proc.poll()}")
        self.flush()

    def terminate(self) -> Callable[[], Any]:
        with self.lock:
            self.win = None
        if self.proc != None:
            self.proc.kill()
            return self.proc.wait
        return lambda: None

    def flush(self):
        with self.lock:
            if self.win is None:
                return
            self.win.clear()
            for i, (line, attr) in enumerate(self.buf):
                self.win.move(i, 0)
                self.win.addstr(line, attr)
            self.win.noutrefresh()
            curses.doupdate()
