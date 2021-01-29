import re

import pytest
import trafaret as t
from monitoring.schema import ToRegexp, SITE_SCHEMA, FILE_SCHEMA


def test_to_regexp_trafaret():
    assert re.compile("test") == ToRegexp().check("test")
    assert re.compile("/^[a-z0-9_-]{3,16}$/") == ToRegexp().check(
        "/^[a-z0-9_-]{3,16}$/"
    )
    with pytest.raises(t.DataError):
        ToRegexp().check("[")
    assert ToRegexp().is_valid("/^[a-z0-9_-]{3,16}$/") is True
    assert ToRegexp().is_valid("[") is False


def test_schema():
    with pytest.raises(t.DataError):
        SITE_SCHEMA.check("test")
    with pytest.raises(t.DataError):
        SITE_SCHEMA.check({"url": "test", "regexp_pattern": "/^[a-z0-9_-]{3,16}$/"})
    assert SITE_SCHEMA.check(
        {"url": "https://google.com", "regexp_pattern": "/^[a-z0-9_-]{3,16}$/"}
    ) == {
        "url": "https://google.com",
        "regexp_pattern": re.compile("/^[a-z0-9_-]{3,16}$/"),
    }
    assert SITE_SCHEMA.check({"url": "https://google.com"}) == {
        "url": "https://google.com",
    }
    assert SITE_SCHEMA.check({"url": "https://google.com", "extra_key": "key"}) == {
        "url": "https://google.com",
    }
    assert FILE_SCHEMA.check([{"url": "https://google.com", "extra_key": "key"}]) == [
        {
            "url": "https://google.com",
        }
    ]
