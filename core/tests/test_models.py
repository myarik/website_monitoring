from core.models import SiteStatus
from core.utils import now


def test_model():
    request_time = now()
    obj = SiteStatus(
        url="https://google.com",
        error=None,
        status_code=200,
        load_time=0.23,
        request_time=request_time,
    )
    assert obj.is_alive
    assert obj.to_dict()["url"] == "https://google.com"
    assert obj.to_dict()["load_time"] == 0.23

    assert isinstance(obj.json_dumps(), str)
    obj2 = SiteStatus.json_load(obj.json_dumps())
    assert obj2.url == "https://google.com"
    assert obj2.request_time[:19] == request_time.isoformat()[:19]

    error_status = SiteStatus(
        url="https://google.com",
        error="error_500",
        status_code=500,
        load_time=0.23,
        request_time=now(),
    )
    assert not error_status.is_alive
