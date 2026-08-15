"""Shared fixtures backed by the fake device served over a real websocket."""

from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import AsyncExitStack
from typing import Any

import pytest
from aiohttp.test_utils import TestServer
from fake_device import FakeStreamMagicDevice, create_app

from aiostreammagic import StreamMagicClient

ConnectClient = Callable[
    [FakeStreamMagicDevice], Coroutine[Any, Any, StreamMagicClient]
]


@pytest.fixture
def device() -> FakeStreamMagicDevice:
    """A fake device seeded with the captured CXN100 payloads."""
    return FakeStreamMagicDevice()


@pytest.fixture
async def connect_client() -> AsyncIterator[ConnectClient]:
    """Factory serving a fake device on localhost and connecting a client to it."""
    async with AsyncExitStack() as stack:

        async def _connect(device: FakeStreamMagicDevice) -> StreamMagicClient:
            server = await stack.enter_async_context(TestServer(create_app(device)))
            client = StreamMagicClient(f"{server.host}:{server.port}")
            await client.connect()
            stack.push_async_callback(client.disconnect)
            return client

        yield _connect


@pytest.fixture
async def client(
    device: FakeStreamMagicDevice, connect_client: ConnectClient
) -> StreamMagicClient:
    """A client connected to the CXN100 fake device."""
    return await connect_client(device)
