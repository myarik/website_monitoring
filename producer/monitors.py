"""
This module represents site inspectors
"""
import asyncio
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import partial
from typing import Dict, Any, Callable

import aiohttp
from aiohttp import ClientSession
from loguru import logger

from core.models import Response
from core.utils import now

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
}


@dataclass
class ProviderList:
    """
    Object for storing provider's name
    """

    HttpMonitor: int  # pylint: disable=invalid-name
    RegexpMonitor: int  # pylint: disable=invalid-name


Provider = ProviderList(0, 1)


@dataclass
class Monitor(ABC):
    """
    Base class for monitoring
    """

    @abstractmethod
    async def check(self, *args: Any, **kwargs: Any) -> Response:
        """
        check a resource
        """
        raise NotImplementedError()


@dataclass
class HttpMonitor(Monitor):
    """
    HttpMonitor a simple http monitor
    """

    headers: Dict[str, str] = field(default_factory=lambda: DEFAULT_HEADERS)

    async def check(  # pylint: disable=arguments-differ
        self, session: ClientSession, *, url: str = None, **kwargs: Any
    ) -> Response:
        """
        Fetching page HTML
        """
        if not url:
            raise TypeError("url doen not set")
        start = now()
        try:
            response = await session.get(url, headers=self.headers)
        except asyncio.TimeoutError:
            logger.warning("cannot reach {}, host does not respond (timeout)", url)
            return Response(
                url,
                error="host does not respond (timeout)",
                status_code=-1,
                load_time=0,
                request_time=now(),
                body=None,
            )
        except aiohttp.ClientError as err:
            logger.warning("cannot reach {}, {}", url, err)
            return Response(
                url,
                error=f"{err}",
                status_code=-1,
                load_time=0,
                request_time=now(),
                body=None,
            )
        load_time = (now() - start).total_seconds()
        logger.debug("{} returns {} -- {}", url, response.status, load_time)
        body = await response.text()
        return Response(
            url,
            error=None if response.ok else f"returns {response.status} response",
            status_code=response.status,
            load_time=load_time,
            request_time=now(),
            body=body,
        )


class RegexpMonitor(HttpMonitor):
    """
    RegexpInspector checks an url and finds a regexp pattern on the page
    """

    async def check(  # pylint: disable=arguments-differ
        self,
        session: ClientSession,
        *,
        url: str = "",
        regexp_pattern: re.Pattern = None,
        **kwargs: Any,
    ) -> Response:
        """
        Fetching page HTML & check the regexp value
        """
        if not regexp_pattern:
            raise TypeError("cannot find a regexp pattern")
        response = await super().check(session, url=url)
        if not response.ok or response.body is None:
            return response
        if regexp_pattern.search(response.body) is not None:
            return response
        response.error = "cannot find a pattern on the page"
        return response


def get_provider_type(item: Dict[str, str]):
    """
    get_provider_type returns a provider base on object
    """
    if isinstance(item.get("regexp_pattern"), re.Pattern):
        return Provider.RegexpMonitor
    return Provider.HttpMonitor


@dataclass
class MonitorFactory:
    """
    factory for storing providers
    """

    def __post_init__(self):
        """
        init a storage
        """
        self._providers: Dict[int, Monitor] = dict()

    def register_format(self, provider_id: int, provider: Monitor):
        """
        register_format adds a provider to a storage
        """
        self._providers[provider_id] = provider

    def _get_provider(self, provider_id: int, item: Dict[str, str]) -> Callable:
        """
        _get_provider returns a callable function base on provider id
        """
        provider = self._providers.get(provider_id)  # pylint: disable=no-member
        if not provider:
            raise ValueError("cannot get a provider")
        return partial(provider.check, **item)

    def get_provider(self, item: Dict[str, str]) -> Callable:
        """
        get_provider returns a callable function
        """
        provider_type = get_provider_type(item)
        return self._get_provider(provider_type, item)


ProviderPool = MonitorFactory()
ProviderPool.register_format(Provider.HttpMonitor, HttpMonitor())
ProviderPool.register_format(Provider.RegexpMonitor, RegexpMonitor())


def get_monitor_instance(item: Dict[str, str]) -> Callable:
    """
    get_monitor_instance returns a callable function
    """
    return ProviderPool.get_provider(item)
