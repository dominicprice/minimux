import curses
from pathlib import Path

import click

from minimux import MiniMux, __version__
from minimux.config import Config


def _main(config_file: Path | None, directory: Path | None):
    # default to current directory
    if directory is None:
        directory = Path(".")

    # attempt to locate minimux.ini, first in current directory then
    # in directory
    if config_file is None:
        if Path("./minimux.ini").exists():
            config_file = Path("./minimux.ini")
        elif (directory / "minimux.ini").exists():
            config_file = directory / "minimux.ini"
        else:
            raise ValueError("could not locate a minimux.ini file")

    # load config
    with open(config_file) as f:
        config = Config.from_file(f, directory)

    # run
    def wrapper(stdscr: "curses.window"):
        minimux = MiniMux(stdscr, config, directory)
        minimux.run()

    curses.wrapper(wrapper)


@click.command("minimux")
@click.version_option(__version__, "--version", "-v")
@click.option(
    "--directory",
    "-d",
    type=click.Path(
        exists=True,
        file_okay=False,
        path_type=Path,
    ),
    default=None,
)
@click.argument(
    "config_file",
    type=click.Path(
        exists=True,
        dir_okay=False,
        path_type=Path,
    ),
    required=False,
    default=None,
)
def main(config_file: Path | None, directory: Path | None):
    try:
        _main(config_file, directory)
    except Exception as e:
        exit("minimux: fatal: " + str(e))
    except:
        exit("minimux: fatal: an unhandled exception occurred")


if __name__ == "__main__":
    main()
