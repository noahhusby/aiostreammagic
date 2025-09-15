import pytest
from aiohttp import ClientSession
from aiostreammagic.stream_magic import StreamMagicClient


# Set your device IP here or use an environment variable
DEVICE_HOST = "192.168.1.29"


@pytest.mark.asyncio
async def test_connect_and_get_info() -> None:
    async with ClientSession() as session:
        client = StreamMagicClient(DEVICE_HOST, session=session)
        connected = await client.connect()
        assert connected is True
        info = client.info
        assert info.model is not None
        assert info.api_version is not None
        await client.disconnect()


@pytest.mark.asyncio
async def test_get_state() -> None:
    async with ClientSession() as session:
        client = StreamMagicClient(DEVICE_HOST, session=session)
        await client.connect()
        state = client.state
        assert state is not None
        await client.disconnect()
