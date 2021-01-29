#!/usr/bin/env python3
"""See the docstring to main()."""
from pathlib import Path

import click

from monitoring.processor import run_app as run_monitoring

CURRENT_DIR = Path(__file__).parent


@click.group()
def main():
    """
    Usage: ./main.py COMMAND [ARG...]

    Commands:

        monitoring   Start a monitoring service\n
            --source-file filepath to the source file
            --debug run application in the debug mode

    Example:\n
        >>> ./main.py monitoring --debug \n
    """


@click.command()
@click.option(
    "--source-file",
    help="Read websites from this file",
    default=str(CURRENT_DIR / "monitoring-sites.json"),
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    show_default=True,
)
@click.option("--debug", default=False, show_default=True, is_flag=True)
def monitoring(source_file: str, debug: bool) -> None:
    """
    This is a module that implements the site checker and sends data to the Kafka.

    The input file is a JSON-format file that you may produce and modify with
    any convenient text editor. The file should have the following format:

        {
            "url": <url>,
            "validator": <regexp>
        }
    """
    click.echo("Starting consumer ...")
    run_monitoring(source_file, debug=debug)


main.add_command(monitoring)

if __name__ == "__main__":
    main()
