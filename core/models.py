"""
This module represents a site status
"""
import json
from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar, Optional, Dict, Any, Type

from core.utils import JSONEncoder

ResponseObj = TypeVar("ResponseObj", bound="Response")


@dataclass
class Response:
    """
    SiteStatus represents a site's analysis status
    """

    url: str
    request_time: datetime
    error: Optional[str] = None
    status_code: Optional[int] = None
    load_time: Optional[float] = None
    body: Optional[str] = None

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
    def ok(self) -> bool:
        """
        returns is_alive status
        """
        return self.error is None

    @classmethod
    def json_load(cls: Type[ResponseObj], data: str) -> ResponseObj:
        """
        creates a class from the  JSON formatted ``str``
        """
        data = json.loads(data)
        return cls(**data)

    def serialize(self):
        return bytes(self.json_dumps(), "utf-8")
