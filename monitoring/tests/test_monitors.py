import asyncio
import re

import aiohttp
import pytest

from monitoring.monitors import HttpMonitor, RegexpMonitor, get_monitor_instance


@pytest.mark.asyncio
async def test_simple_inspector_200(aioresponses):
    aioresponses.get("http://getstatuscode.com/200", status=200, body="test")
    client = HttpMonitor()
    async with aiohttp.ClientSession() as session:
        resp = await client.check(session, url="http://getstatuscode.com/200")
        assert resp.url == "http://getstatuscode.com/200"
        assert resp.status_code == 200
        assert resp.ok


@pytest.mark.asyncio
async def test_simple_inspector_400(aioresponses):
    aioresponses.get("http://getstatuscode.com/400", body="test", status=400)
    client = HttpMonitor()
    async with aiohttp.ClientSession() as session:
        resp = await client.check(session, url="http://getstatuscode.com/400")
        assert resp.url == "http://getstatuscode.com/400"
        assert resp.status_code == 400
        assert not resp.ok


@pytest.mark.asyncio
async def test_simple_inspector_500(aioresponses):
    aioresponses.get("http://getstatuscode.com/500", body="test", status=500)
    client = HttpMonitor()
    async with aiohttp.ClientSession() as session:
        resp = await client.check(session, url="http://getstatuscode.com/500")
        assert resp.url == "http://getstatuscode.com/500"
        assert resp.status_code == 500
        assert not resp.ok


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
    client = HttpMonitor()
    async with aiohttp.ClientSession() as session:
        resp = await client.check(session, url="http://getstatuscode.com/error")
        assert resp.url == "http://getstatuscode.com/error"
        assert resp.status_code == -1
        assert resp.error == "test error"
        assert not resp.ok

        resp = await client.check(session, url="http://getstatuscode.com/timeout")
        assert resp.url == "http://getstatuscode.com/timeout"
        assert resp.status_code == -1
        assert resp.error == "host does not respond (timeout)"
        assert not resp.ok


@pytest.mark.asyncio
async def test_regexp_inspector_200(aioresponses):
    aioresponses.get(
        "http://getstatuscode.com/200",
        status=200,
        body='Go to <a href="https://example.com/about">Demo</a>',
    )

    aioresponses.get(
        "http://getstatuscode.com/200_error",
        status=200,
        body='Go to <a href="https://site.com/about">Demo</a>',
    )
    client = RegexpMonitor()
    async with aiohttp.ClientSession() as session:
        resp = await client.check(
            session,
            url="http://getstatuscode.com/200",
            regexp_pattern=re.compile(r'href="https://example.com(.*?)"'),
        )
        assert resp.url == "http://getstatuscode.com/200"
        assert resp.status_code == 200
        assert resp.ok

        resp = await client.check(
            session,
            url="http://getstatuscode.com/200_error",
            regexp_pattern=re.compile(r'href="https://example.com(.*?)"'),
        )
        assert resp.url == "http://getstatuscode.com/200_error"
        assert resp.status_code == 200
        assert not resp.ok


@pytest.mark.asyncio
async def test_monitor_factory(aioresponses):
    aioresponses.get(
        "http://getstatuscode.com/200",
        status=200,
        body='Go to <a href="https://example.com/about">Demo</a>',
    )
    aioresponses.get(
        "http://getstatuscode.com/check_regexp",
        status=200,
        body='Go to <a href="https://example.com/about">Demo</a>',
    )
    aioresponses.get(
        "http://getstatuscode.com/check_regexp_error",
        status=200,
        body='Go to <a href="https://example.com/about">Demo</a>',
    )

    provider1 = get_monitor_instance({"url": "http://getstatuscode.com/200"})
    provider2 = get_monitor_instance(
        {
            "url": "http://getstatuscode.com/check_regexp",
            "regexp_pattern": re.compile(r'href="https://example.com(.*?)"'),
        }
    )
    provider3 = get_monitor_instance(
        {
            "url": "http://getstatuscode.com/check_regexp_error",
            "regexp_pattern": re.compile(r'href="https://test.com(.*?)"'),
        }
    )
    async with aiohttp.ClientSession() as session:
        resp = await provider1(session)
        assert resp.url == "http://getstatuscode.com/200"
        assert resp.ok
        resp = await provider2(session)
        assert resp.url == "http://getstatuscode.com/check_regexp"
        assert resp.ok
        resp = await provider3(session)
        assert resp.url == "http://getstatuscode.com/check_regexp_error"
        assert not resp.ok
