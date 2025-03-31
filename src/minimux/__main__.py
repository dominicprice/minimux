import click
from pathlib import Path

from minimux import MiniMux
from minimux.config import Config, MiniMuxConfigParser


@click.command("minimux")
@click.argument(
    "config_file",
    type=click.Path(
        exists=True,
        dir_okay=False,
        path_type=Path,
    ),
)
def main(config_file: Path):
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
