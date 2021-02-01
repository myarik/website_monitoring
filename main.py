#!/usr/bin/env python3
"""See the docstring to main()."""
from pathlib import Path

import click

from monitoring.processor import run_app as run_monitoring
from consumer.consumer import run_app as run_consumer
from consumer.migrations.init import run as run_migration

CURRENT_DIR = Path(__file__).parent


@click.group()
def main():
    """
    Usage: ./main.py COMMAND [ARG...]

    Commands:

        monitoring   Start a monitoring service\n
            --source-file filepath to the source file \n
            --kafka_servers kafka bootstrap_servers \n
            --kafka_topic kafka topic \n
            --kafka_ssl_cafile CA certificate \n
            --kafka_ssl_certfile access certificate \n
            --kafka_ssl_keyfile access key \n
            --debug run application in the debug mode \n

        consumer Service for storing monitoring data \n
            --kafka_servers kafka bootstrap_servers \n
            --kafka_topic kafka topic \n
            --kafka_ssl_cafile CA certificate \n
            --kafka_ssl_certfile access certificate \n
            --kafka_ssl_keyfile access key \n
            --postgres_host PostgreSQL hostname \n
            --postgres_port PostgreSQL port \n
            --postgres_db PostgreSQL database \n
            --postgres_user PostgreSQL user \n
            --postgres_password PostgreSQL password \n
            --debug run application in the debug mode \n

        init-migration runs an init migration \n
            --postgres_host PostgreSQL hostname \n
            --postgres_port PostgreSQL port \n
            --postgres_db PostgreSQL database \n
            --postgres_user PostgreSQL user \n
            --postgres_password PostgreSQL password \n

    Example:\n
        >>> ./main.py monitoring --debug \n
        >>> ./main.py consumer --debug \n
        >>> ./main.py init-migration\n
    """


@click.command()
@click.option(
    "--source-file",
    help="Read websites from this file",
    default=str(CURRENT_DIR / "monitoring-sites.json"),
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    show_default=True,
)
@click.option("--kafka_servers", default="kafka:9093")
@click.option("--kafka_topic", default="monitoring")
@click.option(
    "--kafka_ssl_cafile",
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
)
@click.option(
    "--kafka_ssl_certfile",
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
)
@click.option(
    "--kafka_ssl_keyfile",
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
)
@click.option("--debug", default=False, show_default=True, is_flag=True)
def monitoring(
    source_file: str,
    kafka_servers: str,
    kafka_topic: str,
    kafka_ssl_cafile: str,
    kafka_ssl_certfile: str,
    kafka_ssl_keyfile: str,
    debug: bool,
) -> None:
    """
    Service checks sites and sends result to Kafka

    The input file is a JSON-format file that you may produce and modify with
    any convenient text editor. The file should have the following format:

        {
            "url": <url>,
            "validator": <regexp>
        }
    """
    click.echo("Starting monitoring service ...")
    run_monitoring(
        source_file,
        kafka_servers=kafka_servers,
        kafka_topic=kafka_topic,
        kafka_ssl_cafile=kafka_ssl_cafile,
        kafka_ssl_certfile=kafka_ssl_certfile,
        kafka_ssl_keyfile=kafka_ssl_keyfile,
        debug=debug,
    )


@click.command()
@click.option("--kafka_servers", default="kafka:9093")
@click.option("--kafka_topic", default="monitoring")
@click.option(
    "--kafka_ssl_cafile",
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
)
@click.option(
    "--kafka_ssl_certfile",
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
)
@click.option(
    "--kafka_ssl_keyfile",
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
)
@click.option("--postgres_host", default="postgres")
@click.option("--postgres_port", default=5432)
@click.option("--postgres_db", default="monitoring")
@click.option("--postgres_user", default="demo")
@click.option("--postgres_password", default="demopassword")
@click.option("--postgres_ssl", default=False, show_default=True, is_flag=True)
@click.option("--debug", default=False, show_default=True, is_flag=True)
def consumer(
    kafka_servers: str,
    kafka_topic: str,
    kafka_ssl_cafile: str,
    kafka_ssl_certfile: str,
    kafka_ssl_keyfile: str,
    postgres_host: str,
    postgres_port: int,
    postgres_db: str,
    postgres_user: str,
    postgres_password: str,
    postgres_ssl: bool,
    debug: bool,
) -> None:
    """
    Service reads data from Kafka and writes to the database
    """
    click.echo("Starting consumer service ...")
    run_consumer(
        kafka_servers=kafka_servers,
        kafka_topic=kafka_topic,
        kafka_ssl_cafile=kafka_ssl_cafile,
        kafka_ssl_certfile=kafka_ssl_certfile,
        kafka_ssl_keyfile=kafka_ssl_keyfile,
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        postgres_db=postgres_db,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
        postgres_ssl=postgres_ssl,
        debug=debug,
    )


@click.command()
@click.option("--postgres_host", default="postgres")
@click.option("--postgres_port", default=5432)
@click.option("--postgres_db", default="monitoring")
@click.option("--postgres_user", default="demo")
@click.option("--postgres_password", default="demopassword")
@click.option("--postgres_ssl", default=False, show_default=True, is_flag=True)
def init_migration(
    postgres_host: str,
    postgres_port: int,
    postgres_db: str,
    postgres_user: str,
    postgres_password: str,
    postgres_ssl: bool,
) -> None:
    """
    runs init migration
    """
    click.echo("runs a migration ...")
    run_migration(
        postgres_host,
        postgres_port,
        postgres_db,
        postgres_user,
        postgres_password,
        postgres_ssl,
    )


main.add_command(monitoring)
main.add_command(consumer)
main.add_command(init_migration)

if __name__ == "__main__":
    main()
