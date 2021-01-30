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

DEFAULT_TIMEOUT = 10
DEFAULT_CHECK_PERIOD = 5
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


async def _run_app(sources: List[Dict[str, str]]):

    queue: asyncio.Queue[Response] = asyncio.Queue(maxsize=512)
    # create workers to process the queue.
    for index in range(DEFAULT_WORKERS):
        asyncio.create_task(run_worker(index, queue))

    # create callable objects to check a source
    monitors = [get_monitor_instance(source) for source in sources]
    timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        await _run_monitoring(queue, DEFAULT_CHECK_PERIOD, session, monitors)


def run_app(
    source_file: str,
    *,
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
        raw_data = r.read()

    logger.debug(raw_data)
    try:
        main_task = loop.create_task(_run_app(raw_data))
        loop.run_until_complete(main_task)
    except KeyboardInterrupt:  # pragma: no cover
        pass
    finally:
        _cancel_tasks({main_task}, loop)
        _cancel_tasks(asyncio.all_tasks(loop), loop)
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        asyncio.set_event_loop(None)
