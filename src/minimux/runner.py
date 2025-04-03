import atexit
import curses
import subprocess
import threading
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

        rules = {r: a(colour_manager) for r, a in command.rules.items()}
        self.buf = Buffer(0, 0, rules)

    def init(self, stdscr: "curses._CursesWindow", bounds: WindowBounds):
        with self.lock:
            if self.win is not None:
                del self.win
            self.win = stdscr.subwin(*bounds)
            self.win.bkgdset(" ", self.bkgd)
            pt, pr, pb, pl = self.command.padding
            self.buf.resize(
                maxrows=bounds[0] - pt - pb,
                maxcols=bounds[1] - pl - pr,
            )
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
                shell=self.command.shell,
                text=True,
            )

            # ensure the program is terminated at exit
            atexit.register(self.proc.kill)

            # ensure we are connected to stdin/stdout
            assert self.proc.stdin is not None
            assert self.proc.stdout is not None
        except Exception as e:
            self.buf.push("error: failed to start process: " + str(e))
            self.flush()
            return

        if self.command.input is not None:
            self.proc.stdin.write(self.command.input + "\n")
            self.proc.stdin.flush()
        self.proc.stdin.close()

        while self.proc.poll() is None:
            stdout = self.proc.stdout.readline().rstrip()
            self.buf.push(stdout)
            self.flush()

        for line in self.proc.stdout.readlines():
            self.buf.push(line.rstrip())

        self.buf.push(f"** Process exited with status code {self.proc.poll()} **")
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
                self.win.move(
                    i + self.command.padding[0],
                    self.command.padding[3],
                )
                self.win.addstr(line, attr)
            self.win.refresh()
            curses.doupdate()
