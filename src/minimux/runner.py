import atexit
import curses
import os
import subprocess
import threading
import time
from typing import Callable

from minimux.attr import Attr
from minimux.buffer import Buffer
from minimux.colour import ColourManager
from minimux.config import Config
from minimux.range import Range2d

MAX_READ_BUFFER = 1024


class Runner:
    def __init__(
        self,
        command: Config.Command,
        doupdate: Callable[[], None],
        colour_manager: ColourManager,
    ):
        self.command = command
        self.doupdate = doupdate
        self.win: "curses.window | None" = None
        self.colour_manager = colour_manager
        self.buf = Buffer(0, 0, command.tabsize)
        self._stopped = threading.Event()
        self.err: Exception | None = None
        self.lock = threading.Lock()

    def init(self, stdscr: "curses.window", bounds: Range2d):
        "Set the curses window for the runner"
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
                maxcols=bounds.cols.length - self.command.padding.horizontal,
            )
        self._flush()

    def start(self) -> Callable[[], Exception | None]:
        "Start the runner in a background thread, returns immediately"

        def run_safe():
            try:
                self.run()
            except Exception as e:
                self.err = e
            except:
                self.err = RuntimeError("unhandled error")

        t = threading.Thread(target=run_safe)
        t.start()

        def join():
            t.join(5)
            return self.err

        return join

    def stop(self):
        self._stopped.set()

    def run(self):
        "Start the runner until the process exits"
        self._stopped.clear()
        next_launch = time.time()

        while not self._stopped.wait(next_launch - time.time()):
            self._clear()
            next_launch = time.time() + self.command.watch

            # spawn the process
            proc = subprocess.Popen(
                self.command.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                cwd=self.command.cwd,
            )

            def terminate():
                if proc.stdout:
                    proc.stdout.close()
                if proc.stdin:
                    proc.stdin.close()
                proc.terminate()

            # ensure process is terminated at program exit
            atexit.register(terminate)

            # if we are watching, ensure it is terminated when we need
            # the loop to next execute
            timer: threading.Timer | None = None
            if self.command.watch > 0:
                timer = threading.Timer(self.command.watch, terminate)
                timer.start()

            # poll for process output
            return_code = self._poll_process(proc)

            # cancel the timer
            if timer is not None:
                timer.cancel()

            # unregister terminate function at program exit
            atexit.unregister(terminate)

            # stop loop if we are not watching the output
            if self.command.watch <= 0:
                self._write(f"** Exited with return code {return_code} **")
                return

    def _poll_process(self, proc: subprocess.Popen[str]) -> int:
        if proc.stdin is None:
            self._write("error: could not grab a handle to stdin\n")
            return -1
        if proc.stdout is None:
            self._write("error: could not grab a handle to stdout\n")
            return -1

        # send input to command's stdin
        if self.command.input is not None:
            proc.stdin.write(self.command.input + "\n")
            proc.stdin.flush()

        # close stdin unless instructed not to
        if not self.command.no_close_stdin:
            proc.stdin.close()

        # poll process for output
        fileno = proc.stdout.fileno()
        while line := os.read(fileno, MAX_READ_BUFFER):
            self._write(line)

        # ensure process is terminated and write output code to buffer
        return proc.wait()

    def _write(self, data: str | bytes):
        if isinstance(data, bytes):
            data = data.decode(self.command.charset, errors="replace")
        with self.lock:
            self.buf.push(data)
        self._flush()

    def _clear(self):
        with self.lock:
            self.buf.reset()

    def _flush(self):
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
                    try:
                        self.win.addch(char.data, attr(self.colour_manager))
                    except curses.error:
                        # trying to write to the bottom-right corner
                        # raises an error after the character is added
                        # https://docs.python.org/3/library/curses.html#curses.window.addch
                        if row == self.buf.rows - 1 and col == self.buf.cols - 1:
                            pass
                        else:
                            raise
            self.win.noutrefresh()
        self.doupdate()
