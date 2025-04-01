from pathlib import Path

import click

from minimux import MiniMux, __version__
from minimux.config import Config, MiniMuxConfigParser


@click.command("minimux")
@click.option("--version", "-v", is_flag=True)
@click.argument(
    "config_file",
    type=click.Path(
        exists=True,
        dir_okay=False,
        path_type=Path,
    ),
)
def main(config_file: Path, version: bool):
    if version:
        print(__version__)
        exit(0)
    # load config
    parser = MiniMuxConfigParser()
    with open(config_file) as f:
        parser.read_file(f)
    config = Config.from_parser(parser)

    # run
    try:
        minimux = MiniMux(config)
        minimux.run()
    except Exception as e:
        exit(str(e))


if __name__ == "__main__":
    main()
