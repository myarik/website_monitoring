import requests

from producer.inspector import SimpleInspector


def test_simple_inspector_200(requests_mocker):
    requests_mocker.get("http://getstatuscode.com/200", text="test")
    client = SimpleInspector()
    resp = client("http://getstatuscode.com/200")
    assert resp.url == "http://getstatuscode.com/200"
    assert resp.status_code == 200
    assert resp.is_alive


def test_simple_inspector_400(requests_mocker):
    requests_mocker.get("http://getstatuscode.com/400", text="test", status_code=400)
    client = SimpleInspector()
    resp = client("http://getstatuscode.com/400")
    assert resp.url == "http://getstatuscode.com/400"
    assert resp.status_code == 400
    assert not resp.is_alive


def test_simple_inspector_500(requests_mocker):
    requests_mocker.get("http://getstatuscode.com/500", text="test", status_code=500)
    client = SimpleInspector()
    resp = client("http://getstatuscode.com/500")
    assert resp.url == "http://getstatuscode.com/500"
    assert resp.status_code == 500
    assert not resp.is_alive


def test_simple_inspector_timeout(requests_mocker):
    requests_mocker.get(
        "http://getstatuscode.com/timeout",
        exc=requests.exceptions.ConnectTimeout,
    )
    client = SimpleInspector()
    resp = client("http://getstatuscode.com/timeout")
    assert resp.url == "http://getstatuscode.com/timeout"
    assert resp.status_code == -1
    assert resp.error == "timeout"
    assert not resp.is_alive
