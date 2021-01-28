"""
This module represents site inspectors
"""
from dataclasses import dataclass, field
from typing import Dict, Any

import requests
from loguru import logger

from core.models import SiteStatus

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
    timeout: int = DEFAULT_TIMEOUT
    headers: Dict[str, str] = field(default_factory=lambda: DEFAULT_HEADERS)

    def __call__(self, url: str, *args: Any, **kwargs: Any) -> SiteStatus:
        try:
            response = requests.get(url, timeout=self.timeout, headers=self.headers)
        except requests.exceptions.SSLError:
            logger.error("{} returns the SSLError", url)
            return SiteStatus(url, error="ssl_error", status_code=-1, load_time=0)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            logger.error("{} does not respond", url)
            return SiteStatus(url, error="timeout", status_code=-1, load_time=0)

        if not response.ok:
            return SiteStatus(
                url,
                error=f"error_{response.status_code}",
                status_code=response.status_code,
                load_time=response.elapsed.total_seconds(),
            )
        return SiteStatus(
            url,
            error=None,
            status_code=response.status_code,
            load_time=response.elapsed.total_seconds(),
        )
