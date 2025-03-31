import threading
import subprocess
import curses
from typing import Any, Callable

from minimux.buffer import Buffer
from minimux.colour import ColourManager
from minimux.config import Command


class Runner:
    def __init__(
        self,
        command: Command,
        lock: threading.Lock,
        colour_manager: ColourManager,
        win: "curses._CursesWindow",
    ):
        self.command = command
        self.lock = lock
        self.win = win
        self.proc: subprocess.Popen[str] | None = None
        self.active = True

        rows, cols = win.getmaxyx()
        self.buf = Buffer(
            cols,
            rows,
            {k: v(colour_manager) for k, v in command.rules.items()},
        )

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
        self.active = False
        if self.proc != None:
            self.proc.kill()
            return self.proc.wait
        return lambda: None

    def flush(self):
        if not self.active:
            return

        with self.lock:
            self.win.clear()
            for i, (line, attr) in enumerate(self.buf):
                self.win.move(i, 0)
                self.win.addstr(line, attr)
            self.win.noutrefresh()
            curses.doupdate()
