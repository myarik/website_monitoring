"""
This module represents a source schema
"""
import re
from functools import partial
from typing import Any

import trafaret as t

OptKey = partial(t.Key, optional=True)


class ToRegexp(t.String):
    """
    Checks that value is a valid regex and convers string to regexp

    >>> ToRegexp().check("/^[a-z0-9_-]{3,16}$/")
    re.compile(r'/^[a-z0-9_-]{3,16}$/', re.UNICODE)
    >>> ToRegexp().is_valid("/^[a-z0-9_-]{3,16}$/")
    True
    >>> ToRegexp().is_valid("[")
    False
    """
    def check_and_return(self, value: Any) -> re.Pattern:
        regexp_pattern = super().check_and_return(value)
        try:
            return re.compile(regexp_pattern)
        except re.error:
            self._failure(
                "only regexp pattern is allowed",
                value=value,
                code="is_not_regexp_pattern",
            )

    def __repr__(self) -> str:
        return "<ToRegexp>"


SITE_SCHEMA = t.Dict(
    {
        t.Key("url"): t.URL,
        OptKey("regexp_pattern"): ToRegexp,
    }
).ignore_extra("*")

FILE_SCHEMA = t.List(SITE_SCHEMA)
