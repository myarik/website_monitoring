"""
This module represents writers
"""
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from aiokafka import AIOKafkaProducer

from loguru import logger


@dataclass
class BaseWriter(ABC):
    """
    Base class for writer
    """

    @abstractmethod
    async def write(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        check a resource
        """
        raise NotImplementedError()


@dataclass
class KafkaWriter(BaseWriter):
    """
    Kafka writer
    """

    bootstrap_servers: str
    topic: str
    producer: AIOKafkaProducer = field(init=False)

    def __post_init__(self):
        loop = asyncio.get_event_loop()
        self.producer = AIOKafkaProducer(
            loop=loop, bootstrap_servers=self.bootstrap_servers
        )

    async def start(self):
        """
        Get cluster layout and initial topic/partition leadership information
        """
        await self.producer.start()

    async def stop(self):
        """
        stopping kafka producer
        """
        await self.producer.stop()
        logger.debug("Stopping kafka producer...")

    async def write(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        check a resource
        """
        await self.producer.send_and_wait(self.topic, message)
        logger.debug("Sent message {} sent", message)
