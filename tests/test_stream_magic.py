from typing import Any, cast

import pytest
from aiohttp import ClientSession

from aiostreammagic.stream_magic import StreamMagicClient, _WEBSOCKET_HEARTBEAT


class FakeSession:
    def __init__(self) -> None:
        self.closed = False
        self.close_calls = 0
        self.ws_connect_calls: list[dict[str, Any]] = []

    async def close(self) -> None:
        self.close_calls += 1
        self.closed = True

    async def ws_connect(self, uri: str, **kwargs: Any) -> object:
        self.ws_connect_calls.append({"uri": uri, "kwargs": kwargs})
        return object()


@pytest.mark.asyncio
async def test_disconnect_does_not_close_injected_session_when_disabled() -> None:
    session = FakeSession()
    client = StreamMagicClient(
        "192.0.2.10",
        cast(ClientSession, session),
        should_close_session=False,
    )

    await client.disconnect()

    assert session.close_calls == 0
    assert client.session is session


@pytest.mark.asyncio
async def test_disconnect_closes_injected_session_by_default() -> None:
    session = FakeSession()
    client = StreamMagicClient("192.0.2.10", cast(ClientSession, session))

    await client.disconnect()

    assert session.close_calls == 1
    assert client.session is None


@pytest.mark.asyncio
async def test_disconnect_closes_session_created_by_client() -> None:
    session = FakeSession()
    client = StreamMagicClient("192.0.2.10")
    client.session = cast(ClientSession, session)

    await client.disconnect()

    assert session.close_calls == 1
    assert client.session is None


@pytest.mark.asyncio
async def test_ws_connect_uses_heartbeat() -> None:
    session = FakeSession()
    client = StreamMagicClient("192.0.2.10", cast(ClientSession, session))

    await client._ws_connect("ws://192.0.2.10/smoip")

    assert session.ws_connect_calls == [
        {
            "uri": "ws://192.0.2.10/smoip",
            "kwargs": {
                "headers": {
                    "Origin": "ws://192.0.2.10",
                    "Host": "192.0.2.10:80",
                },
                "heartbeat": _WEBSOCKET_HEARTBEAT,
            },
        }
    ]
