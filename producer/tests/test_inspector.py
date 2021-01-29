import asyncio

import aiohttp
import pytest

from producer.inspector import SimpleInspector


@pytest.mark.asyncio
async def test_simple_inspector_200(aioresponses):
    aioresponses.get("http://getstatuscode.com/200", status=200, body="test")
    client = SimpleInspector()
    async with aiohttp.ClientSession() as session:
        resp = await client("http://getstatuscode.com/200", session)
        assert resp.url == "http://getstatuscode.com/200"
        assert resp.status_code == 200
        assert resp.is_alive


@pytest.mark.asyncio
async def test_simple_inspector_400(aioresponses):
    aioresponses.get("http://getstatuscode.com/400", body="test", status=400)
    client = SimpleInspector()
    async with aiohttp.ClientSession() as session:
        resp = await client("http://getstatuscode.com/400", session)
        assert resp.url == "http://getstatuscode.com/400"
        assert resp.status_code == 400
        assert not resp.is_alive


@pytest.mark.asyncio
async def test_simple_inspector_500(aioresponses):
    aioresponses.get("http://getstatuscode.com/500", body="test", status=500)
    client = SimpleInspector()
    async with aiohttp.ClientSession() as session:
        resp = await client("http://getstatuscode.com/500", session)
        assert resp.url == "http://getstatuscode.com/500"
        assert resp.status_code == 500
        assert not resp.is_alive


@pytest.mark.asyncio
async def test_simple_inspector_exception(aioresponses):
    aioresponses.get(
        "http://getstatuscode.com/timeout",
        exception=asyncio.TimeoutError("test error"),
    )
    aioresponses.get(
        "http://getstatuscode.com/error",
        exception=aiohttp.ClientError("test error"),
    )
    client = SimpleInspector()
    async with aiohttp.ClientSession() as session:
        resp = await client("http://getstatuscode.com/error", session)
        assert resp.url == "http://getstatuscode.com/error"
        assert resp.status_code == -1
        assert resp.error == "test error"
        assert not resp.is_alive

        resp = await client("http://getstatuscode.com/timeout", session)
        assert resp.url == "http://getstatuscode.com/timeout"
        assert resp.status_code == -1
        assert resp.error == "host does not respond (timeout)"
        assert not resp.is_alive
