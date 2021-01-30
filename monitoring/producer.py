"""
Module for sending data to kafka
"""
from __future__ import annotations
import asyncio

from loguru import logger
from core.models import Response


async def run_worker(worker_id: int, queue: asyncio.Queue[Response]) -> None:
    """
    Send a response to kafka
    """
    while True:
        response = await queue.get()
        logger.debug(
            "[{}]result received {} -- {}", worker_id, response.url, response.ok
        )
        queue.task_done()
