"""
This module represents writers
"""
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from aiokafka import AIOKafkaProducer
from aiokafka.helpers import create_ssl_context

from loguru import logger


@dataclass
class BaseWriter(ABC):
    """
    Base class for writer
    """

    @abstractmethod
    async def write(self, message: bytes, *args: Any, **kwargs: Any) -> None:
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
    kafka_ssl_cafile: str = None
    kafka_ssl_certfile: str = None
    kafka_ssl_keyfile: str = None
    producer: AIOKafkaProducer = field(init=False)

    def __post_init__(self):
        loop = asyncio.get_event_loop()

        if not self.kafka_ssl_cafile:
            self.producer = AIOKafkaProducer(
                loop=loop, bootstrap_servers=self.bootstrap_servers
            )
        else:
            context = create_ssl_context(
                cafile=self.kafka_ssl_cafile,
                certfile=self.kafka_ssl_certfile,
                keyfile=self.kafka_ssl_keyfile,
            )
            self.producer = AIOKafkaProducer(
                loop=loop,
                bootstrap_servers=self.bootstrap_servers,
                security_protocol="SSL",
                ssl_context=context,
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

    async def write(self, message: bytes, *args: Any, **kwargs: Any) -> None:
        """
        check a resource
        """
        await self.producer.send_and_wait("monitoring", message)
        logger.debug("Sending event: {}", message)
