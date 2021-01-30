"""
Module for sending data to kafka
"""
from __future__ import annotations
import asyncio

from loguru import logger
from core.models import Response
from monitoring.writers import BaseWriter


async def run_worker(
    worker_id: int, queue: asyncio.Queue[Response], writer: BaseWriter
) -> None:
    """
    Send a response to kafka
    """
    while True:
        response = await queue.get()
        logger.debug(f"[{worker_id}] message received")
        # create the message
        message = response.serialize()
        await writer.write(message)
        queue.task_done()
