import atexit
import curses
import os
import subprocess
import threading
from typing import Any, Callable

from minimux.attr import Attr
from minimux.buffer import Buffer
from minimux.colour import ColourManager
from minimux.config import Config
from minimux.range import Range2d
from minimux.utils import debug

MAX_READ_BUFFER = 1024


class Runner:
    def __init__(
        self,
        command: Config.Command,
        doupdate: Callable[[], None],
        colour_manager: ColourManager,
    ):
        self.command = command
        self.lock = threading.Lock()
        self.doupdate = doupdate
        self.win: "curses.window | None" = None
        self.proc: subprocess.Popen[str] | None = None
        self.colour_manager = colour_manager
        self.buf = Buffer(0, 0)

    def init(self, stdscr: "curses.window", bounds: Range2d):
        with self.lock:
            if self.win is not None:
                del self.win
            self.win = stdscr.subwin(
                bounds.rows.length,
                bounds.cols.length,
                bounds.rows.start,
                bounds.cols.start,
            )
            bkgd = self.command.attr(self.colour_manager)
            self.win.bkgdset(" ", bkgd)
            self.win.bkgd(" ", bkgd)
            self.buf.resize(
                maxrows=bounds.rows.length - self.command.padding.vertical,
                maxcols=bounds.cols.length - self.command.padding.horizontal - 1,
            )
        self.flush()

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
                cwd=self.command.cwd,
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
            for row, line in enumerate(self.buf.lines()):
                for col, char in enumerate(line):
                    attr = self.command.attr | Attr.from_char(char)
                    self.win.move(
                        self.command.padding.top + row,
                        self.command.padding.left + col,
                    )
                    debug(
                        "trying to add char '" + char.data + "' with attr",
                        attr(self.colour_manager),
                        "to position row =",
                        row,
                        "and col =",
                        col,
                        name=self.command.name,
                    )
                    self.win.addch(char.data, attr(self.colour_manager))
            self.win.noutrefresh()
        self.doupdate()
