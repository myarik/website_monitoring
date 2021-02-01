"""
Create a monitoring table
"""
import asyncio

import asyncpg
from loguru import logger

CREATE_MONITORING_TABLE = """
    CREATE TABLE IF NOT EXISTS monitoring(
        id SERIAL PRIMARY KEY,
        url VARCHAR(1500) NOT NULL,
        load_time  numeric(10,2) NOT NULL,
        status_code smallint NOT NULL,
        is_alive boolean NOT NULL,
        error TEXT NULL,
        request_date TIMESTAMPTZ
    );
    """

CREATE_SIMPLE_INDEX = """
    CREATE INDEX idx_monitoring_name on monitoring (url, request_date);
"""


async def main(
    host: str, port: int, database: str, user: str, password: str, ssl: bool
):
    """
    create a table
    """
    pg_connection_params = {
        "host": host,
        "port": port,
        "user": user,
        "database": database,
        "password": password,
    }

    if ssl:
        ctx = ssl.create_default_context(cafile="")
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        pg_connection_params["ssl"] = ctx

    connection = await asyncpg.connect(**pg_connection_params)
    statements = [CREATE_MONITORING_TABLE, CREATE_SIMPLE_INDEX]

    logger.info("Creating the product database...")
    for statement in statements:
        status = await connection.execute(statement)
        print(status)
    logger.info("Finished creating the product database!")
    await connection.close()


def run(host: str, port: int, database: str, user: str, password: str, postgres_ssl: bool):
    """
    run a migration
    """
    asyncio.run(main(host, port, database, user, password, postgres_ssl))
