"""
This module represents site inspectors
"""
import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any

import aiohttp
from aiohttp import ClientSession
from loguru import logger

from core.models import SiteStatus
from core.utils import now

DEFAULT_TIMEOUT = 10
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
}


@dataclass
class SimpleInspector:
    """
    SimpleInspector a simple site checker
    """

    headers: Dict[str, str] = field(default_factory=lambda: DEFAULT_HEADERS)

    async def __call__(
        self, url: str, session: ClientSession, *args: Any, **kwargs: Any
    ) -> SiteStatus:
        """
        Fetching page HTML
        """
        start = now()
        try:
            response = await session.get(url, headers=self.headers)
        except asyncio.TimeoutError:
            logger.warning("cannot reach {}, host does not respond (timeout)", url)
            return SiteStatus(
                url,
                error="host does not respond (timeout)",
                status_code=-1,
                load_time=0,
                request_time=now(),
            )
        except aiohttp.ClientError as err:
            logger.warning("cannot reach {}, {}", url, err)
            return SiteStatus(
                url,
                error=f"{err}",
                status_code=-1,
                load_time=0,
                request_time=now(),
            )
        load_time = (now() - start).total_seconds()
        if not response.ok:
            logger.warning("{} returns {} -- {}", url, response.status, load_time)
            return SiteStatus(
                url,
                error=f"returns {response.status} response",
                status_code=response.status,
                load_time=load_time,
                request_time=now(),
            )
        logger.debug("{} returns {} -- {}", url, response.status, load_time)
        return SiteStatus(
            url,
            error=None,
            status_code=response.status,
            load_time=load_time,
            request_time=now(),
        )
