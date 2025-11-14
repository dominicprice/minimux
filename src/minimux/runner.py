import atexit
import curses
import subprocess
import threading
import os
from typing import Any, Callable

from minimux.buffer import Buffer
from minimux.colour import ColourManager
from minimux.config import Command
from minimux.utils import WindowBounds, debug


MAX_READ_BUFFER = 1024


class Runner:
    def __init__(
        self,
        command: Command,
        lock: threading.Lock,
        colour_manager: ColourManager,
    ):
        self.command = command
        self.lock = lock
        self.win: "curses.window | None" = None
        self.proc: subprocess.Popen[str] | None = None
        self.bkgd = command.attr(colour_manager)
        self.buf = Buffer(0, 0, colour_manager)

    def init(self, stdscr: "curses.window", bounds: WindowBounds):
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
        self.write("\n\n\n\n\n\n\n\n")

    def start(self):
        t = threading.Thread(target=self.run, daemon=True)
        t.start()

    def run(self):
        try:
            # open the subprocess with pipes to stdout and stdin,
            # redirecting stderr to stdout
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
            # write error to output buffer
            self.write("error: failed to start process: " + str(e))
            return

        # send input to command's stdin
        if self.command.input is not None:
            self.proc.stdin.write(self.command.input + "\n")
            self.proc.stdin.flush()

        # close stdin unless instructed not to
        if not self.command.no_close_stdin:
            self.proc.stdin.close()

        # poll process for output
        fileno = self.proc.stdout.fileno()
        while line := os.read(fileno, MAX_READ_BUFFER):
            debug(
                "got output output",
                line,
                name=self.command.name,
            )
            self.write(line)

        # ensure process is killed
        self.proc.wait()

        # write output code to buffer
        ret = self.proc.poll()
        self.write(f"** Process exited with status code {ret} **")

    def write(self, data: str | bytes):
        if isinstance(data, bytes):
            data = data.decode(self.command.charset, errors="replace")
        with self.lock:
            self.buf.push(data)
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
            debug(
                "flushing with",
                self.buf.screen.lines,
                "x",
                self.buf.screen.columns,
                "buffer and ",
                self.win.getmaxyx(),
                #     "screen and data",
                #     "\n" + "\n".join(self.buf.screen.display),
                name=self.command.name,
            )
            for i, line in enumerate(self.buf):
                self.win.move(
                    i + self.command.padding[0],
                    self.command.padding[3],
                )
                for rt in line.elements:
                    try:
                        self.win.addstr(rt.text, 0)
                    except curses.error:
                        pass
            self.win.refresh()
            curses.doupdate()
