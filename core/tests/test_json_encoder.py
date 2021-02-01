import json

from core.utils import now, JSONEncoder


def test_encoder():
    result = json.dumps({"now": now(), "context": "test"}, cls=JSONEncoder)
    assert isinstance(result, str)
    assert len(result) != 0
