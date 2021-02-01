"""
Module for reading data from Kafka and write them to the PostgreSQL
"""
from __future__ import annotations

import asyncio
import ssl
import sys
from typing import Set, Any, Optional, Callable

import asyncpg
from aiokafka import AIOKafkaConsumer
from aiokafka.helpers import create_ssl_context
from loguru import logger

from consumer.serializer import KafkaDeserializer, REQUEST_SCHEMA
from core.models import Response

DEFAULT_POOL_SIZE = 3
DEFAULT_DB_WORKERS = 3


def _cancel_tasks(to_cancel: Set["asyncio.Task[Any]"], loop: asyncio.AbstractEventLoop):
    if not to_cancel:
        return

    for task in to_cancel:
        task.cancel()

    loop.run_until_complete(
        asyncio.gather(*to_cancel, loop=loop, return_exceptions=True)
    )

    for task in to_cancel:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler(
                {
                    "message": "unhandled exception during asyncio.run() shutdown",
                    "exception": task.exception(),
                    "task": task,
                }
            )


async def kafka_consumer(
    kafka_servers: str,
    kafka_topic: str,
    queue: asyncio.Queue[Response],
    *,
    deserializer: Optional[Callable] = None,
    kafka_ssl_cafile: str = None,
    kafka_ssl_certfile: str = None,
    kafka_ssl_keyfile: str = None,
) -> None:
    """
    kafka_consumer reads data from kafka and send it to a queue
    """
    loop = asyncio.get_event_loop()
    kafka_kwargs = {
        "loop": loop,
        "bootstrap_servers": kafka_servers,
        "client_id": "client-storage",
        "group_id": "my-group",
        "enable_auto_commit": True,
        "auto_commit_interval_ms": 1000,  # Autocommit every second
        "auto_offset_reset": "earliest",  # start from beginning
        "value_deserializer": deserializer,
    }
    if not kafka_ssl_cafile:
        consumer = AIOKafkaConsumer(kafka_topic, **kafka_kwargs)
    else:
        context = create_ssl_context(
            cafile=kafka_ssl_cafile,
            certfile=kafka_ssl_certfile,
            keyfile=kafka_ssl_keyfile,
        )
        consumer = AIOKafkaConsumer(
            kafka_topic,
            security_protocol="SSL",
            ssl_context=context,
            **kafka_kwargs,
        )
    await consumer.start()
    try:
        # Consume messages
        async for msg in consumer:
            if msg.value is not None:
                logger.debug(f"Message received: {msg.value} at {msg.timestamp}")
                try:
                    asyncio.get_event_loop().call_soon_threadsafe(
                        queue.put_nowait, msg.value
                    )
                except asyncio.QueueFull as err:
                    logger.error("queue is full cannot send a response - {}", err)
    finally:
        # Will leave consumer group; perform autocommit if enabled.
        await consumer.stop()


async def run_worker(
    worker_id: int, queue: asyncio.Queue[Response], pool: asyncpg.pool.Pool
) -> None:
    """
    Send a response to kafka
    """
    insert_response = "INSERT INTO monitoring VALUES(DEFAULT, $1, $2, $3, $4, $5, $6)"
    while True:
        response = await queue.get()
        # save a message
        async with pool.acquire() as connection:
            try:
                await connection.execute(
                    insert_response,
                    response.url,
                    response.load_time,
                    response.status_code,
                    response.ok,
                    response.error,
                    response.request_time,
                )
            except asyncpg.exceptions.PostgresConnectionError:
                logger.error(f"[{worker_id}] cannot connect to postgresql")
            except asyncpg.exceptions.DataError as err:
                logger.error(f"[{worker_id}] invalid postgres query {err}")
            except Exception as err:  # pylint: disable=broad-except
                logger.error(f"[{worker_id}] unexpected error {err}")
        queue.task_done()


async def _run_app(
    kafka_servers: str,
    kafka_topic: str,
    postgres_host: str,
    postgres_port: int,
    postgres_db: str,
    postgres_user: str,
    postgres_password: str,
    *,
    deserializer: Optional[Callable] = None,
    postgres_ssl: bool = False,
    kafka_ssl_cafile: str = None,
    kafka_ssl_certfile: str = None,
    kafka_ssl_keyfile: str = None,
) -> None:
    queue: asyncio.Queue[Response] = asyncio.Queue(maxsize=512)
    asyncio.create_task(
        kafka_consumer(
            kafka_servers,
            kafka_topic,
            queue,
            deserializer=deserializer,
            kafka_ssl_cafile=kafka_ssl_cafile,
            kafka_ssl_certfile=kafka_ssl_certfile,
            kafka_ssl_keyfile=kafka_ssl_keyfile,
        )
    )
    pg_connection_params = {
        "host": postgres_host,
        "port": postgres_port,
        "user": postgres_user,
        "database": postgres_db,
        "password": postgres_password,
        "min_size": DEFAULT_POOL_SIZE,
        "max_size": DEFAULT_POOL_SIZE,
    }
    if postgres_ssl:
        ctx = ssl.create_default_context(cafile="")
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        pg_connection_params["ssl"] = ctx

    async with asyncpg.create_pool(**pg_connection_params) as pool:
        worker_tasks = [
            asyncio.create_task(run_worker(index, queue, pool))
            for index in range(DEFAULT_DB_WORKERS)
        ]

        await asyncio.gather(*worker_tasks)


def run_app(
    kafka_servers: str,
    kafka_topic: str,
    postgres_host: str,
    postgres_port: int,
    postgres_db: str,
    postgres_user: str,
    postgres_password: str,
    *,
    postgres_ssl: bool = False,
    kafka_ssl_cafile: str = None,
    kafka_ssl_certfile: str = None,
    kafka_ssl_keyfile: str = None,
    debug: bool = False,
) -> None:
    """run the consumer"""
    loop = asyncio.get_event_loop()
    loop.set_debug(debug)

    logger.remove()
    logger.add(
        sys.stderr,
        colorize=True,
        format="<green>{time}</green> <level>{level}</level>: {message}",
        level="DEBUG" if debug else "INFO",
    )
    deserializer = KafkaDeserializer(REQUEST_SCHEMA)

    try:
        main_task = loop.create_task(
            _run_app(
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
                deserializer=deserializer,
            )
        )
        loop.run_forever()
    except KeyboardInterrupt:  # pragma: no cover
        pass
    finally:
        _cancel_tasks({main_task}, loop)
        _cancel_tasks(asyncio.all_tasks(loop), loop)
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        asyncio.set_event_loop(None)
