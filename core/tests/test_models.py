from core.models import SiteStatus


def test_model():
    obj = SiteStatus(
        url="https://google.com", error=None, status_code=200, load_time=0.23
    )
    assert obj.is_alive
    assert obj.to_dict() == {
        "url": "https://google.com",
        "error": None,
        "status_code": 200,
        "load_time": 0.23,
    }
    assert (
        obj.json_dumps()
        == '{"url": "https://google.com", "error": null, "status_code": 200, '
        '"load_time": 0.23}'
    )
    obj2 = SiteStatus.json_load(obj.json_dumps())
    assert obj2.url == "https://google.com"

    error_status = SiteStatus(
        url="https://google.com", error="error_500", status_code=500, load_time=0.23
    )
    assert not error_status.is_alive
