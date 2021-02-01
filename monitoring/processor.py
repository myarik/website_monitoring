"""
Module for monitoring websites
"""
from __future__ import annotations

import asyncio
import sys
from functools import partial
from typing import List, Dict, Set, Any, Callable

import aiohttp
from aiohttp import ClientSession
from loguru import logger

from core.models import Response
from monitoring.monitors import get_monitor_instance
from monitoring.producer import run_worker
from monitoring.reader import JSONFileReader
from monitoring.schema import FILE_SCHEMA
from monitoring.writers import KafkaWriter

DEFAULT_TIMEOUT = 10
DEFAULT_CHECK_PERIOD = 60
DEFAULT_WORKERS = 3


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


def callback(queue: asyncio.Queue[Response], fut: asyncio.Task):
    """
    callback calls when coroutine returns a result
    """
    try:
        response = fut.result()
    except Exception as err:  # pylint: disable=broad-except
        logger.error("Unexpected error for getting content - {}", err)
        return
    try:
        asyncio.get_event_loop().call_soon_threadsafe(queue.put_nowait, response)
    except asyncio.QueueFull as err:
        logger.error("queue is full cannot send a response - {}", err)


async def _run_monitoring(
    queue,
    period: int,
    session: ClientSession,
    monitors: List[Callable],
):
    """
    Periodically poll for monitoring
    """
    iteration = 1

    while True:
        logger.debug("Checking sites ({})", iteration)
        for monitor in monitors:
            future = asyncio.ensure_future(monitor(session))
            future.add_done_callback(partial(callback, queue))
        logger.debug("Waiting for {} seconds...".format(period))
        iteration += 1
        await asyncio.sleep(period)


async def _run_app(
    sources: List[Dict[str, str]],
    kafka_servers: str,
    kafka_topic: str,
    *,
    kafka_ssl_cafile: str = None,
    kafka_ssl_certfile: str = None,
    kafka_ssl_keyfile: str = None,
):
    queue: asyncio.Queue[Response] = asyncio.Queue(maxsize=512)
    # setup a kafka producer
    producer = KafkaWriter(
        kafka_servers,
        kafka_topic,
        kafka_ssl_cafile=kafka_ssl_cafile,
        kafka_ssl_certfile=kafka_ssl_certfile,
        kafka_ssl_keyfile=kafka_ssl_keyfile,
    )
    await producer.start()
    # create workers to process the queue.
    worker_tasks = []
    for index in range(DEFAULT_WORKERS):
        worker_tasks.append(asyncio.create_task(run_worker(index, queue, producer)))

    # create callable objects to check a source
    monitors = [get_monitor_instance(source) for source in sources]
    timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            await _run_monitoring(queue, DEFAULT_CHECK_PERIOD, session, monitors)
    except asyncio.CancelledError:
        # cancel workers
        for task in worker_tasks:
            task.cancel()
        logger.debug("workers stopped")
        await producer.stop()
        logger.debug("kafka producer stopped")


def run_app(
    source_file: str,
    kafka_servers: str,
    kafka_topic: str,
    *,
    kafka_ssl_cafile: str = None,
    kafka_ssl_certfile: str = None,
    kafka_ssl_keyfile: str = None,
    debug: bool = False,
) -> None:
    """Run an app locally"""
    loop = asyncio.get_event_loop()
    loop.set_debug(debug)

    logger.remove()
    logger.add(
        sys.stderr,
        colorize=True,
        format="<green>{time}</green> <level>{level}</level>: {message}",
        level="DEBUG" if debug else "INFO",
    )

    with JSONFileReader(source_file, FILE_SCHEMA) as r:
        try:
            raw_data = r.read()
        except TypeError:
            return

    logger.debug(raw_data)
    try:
        main_task = loop.create_task(
            _run_app(
                raw_data,
                kafka_servers=kafka_servers,
                kafka_topic=kafka_topic,
                kafka_ssl_cafile=kafka_ssl_cafile,
                kafka_ssl_certfile=kafka_ssl_certfile,
                kafka_ssl_keyfile=kafka_ssl_keyfile,
            )
        )
        loop.run_until_complete(main_task)
    except KeyboardInterrupt:  # pragma: no cover
        pass
    finally:
        _cancel_tasks({main_task}, loop)
        _cancel_tasks(asyncio.all_tasks(loop), loop)
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        asyncio.set_event_loop(None)
