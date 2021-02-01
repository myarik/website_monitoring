"""
This module represents a helper functions
"""
import datetime
import decimal
import json
import uuid

import pytz as pytz

utc = pytz.utc


def now():
    """
    Returns an aware or naive datetime.datetime in UTC.
    """
    return datetime.datetime.utcnow().replace(tzinfo=utc)


class JSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time, decimal types, and
    UUIDs.
    """

    def default(self, o):
        if isinstance(o, datetime.datetime):
            r = o.isoformat()
            return r
        elif isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, (decimal.Decimal, uuid.UUID)):
            return str(o)
        return super().default(o)
