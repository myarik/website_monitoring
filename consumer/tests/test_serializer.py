from consumer.serializer import KafkaDeserializer, REQUEST_SCHEMA


def test_serializer():
    serializer = KafkaDeserializer(REQUEST_SCHEMA)
    assert serializer(b"aa") is None
    assert serializer(b'{"test": "test"}') is None
    response = serializer(
        b'{"url": "https://google.com", "error": null, "status_code": 200, '
        b'"load_time": 0.32332, "request_time": "2021-01-31T07:46:52.504364+00:00"}'
    )
    assert response is not None
    assert response.url == "https://google.com"
    assert response.request_time.isoformat() == "2021-01-31T07:46:52.504364+00:00"

