"""
This module represents a site status
"""
import json
from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar, Optional, Dict, Any, Type

from core.utils import JSONEncoder

SiteStatusObj = TypeVar("SiteStatusObj", bound="SiteStatus")


@dataclass
class SiteStatus:
    """
    SiteStatus represents a site's analysis status
    """

    __slots__ = ["url", "error", "status_code", "load_time", "request_time"]
    url: str
    error: Optional[str]
    status_code: Optional[int]
    load_time: Optional[float]
    request_time: datetime

    def to_dict(self) -> Dict[str, Any]:
        """
        returns a dictionary representation of an object
        """
        return {
            "url": self.url,
            "error": self.error,
            "status_code": self.status_code,
            "load_time": self.load_time,
            "request_time": self.request_time,
        }

    def json_dumps(self) -> str:
        """
        serialize ``obj`` to a JSON formatted ``str``
        """
        return json.dumps(self.to_dict(), cls=JSONEncoder)

    @property
    def is_alive(self) -> bool:
        """
        returns is_alive status
        """
        return self.error is None

    @classmethod
    def json_load(cls: Type[SiteStatusObj], data: str) -> SiteStatusObj:
        """
        creates a class from the  JSON formatted ``str``
        """
        data = json.loads(data)
        return cls(**data)
