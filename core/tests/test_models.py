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
        raw_response=None,
    )
    assert obj.ok
    assert obj.to_dict()["url"] == "https://google.com"
    assert obj.to_dict()["load_time"] == 0.23

    assert isinstance(obj.json_dumps(), str)
    obj2 = Response.json_load(obj.json_dumps())
    assert obj2.url == "https://google.com"
    assert obj2.request_time[:19] == request_time.isoformat()[:19]

    error_status = Response(
        url="https://google.com",
        error="error_500",
        status_code=500,
        load_time=0.23,
        request_time=now(),
        raw_response=None,
    )
    assert not error_status.ok
