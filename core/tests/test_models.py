from core.models import Response
from core.utils import now


def test_model():
    request_time = now()
    obj = Response(
        url="https://google.com",
        error=None,
        status_code=200,
        load_time=0.23,
        request_time=request_time,
        body=None,
    )
    assert obj.ok
    assert obj.to_dict()["url"] == "https://google.com"
    assert obj.to_dict()["load_time"] == 0.23

    assert isinstance(obj.json_dumps(), str)

    error_status = Response(
        url="https://google.com",
        error="error_500",
        status_code=500,
        load_time=0.23,
        request_time=now(),
        body=None,
    )
    assert not error_status.ok
