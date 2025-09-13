import pytest
from aiohttp import ClientSession
from aiostreammagic.stream_magic import StreamMagicClient
from packaging.version import Version


# Set your device IP here or use an environment variable
DEVICE_HOST = "192.168.1.29"


@pytest.mark.asyncio
async def test_connect_and_get_info():
    async with ClientSession() as session:
        client = StreamMagicClient(DEVICE_HOST, session=session)
        connected = await client.connect()
        assert connected is True
        info = client.info
        assert info.model is not None
        assert info.api_version is not None
        await client.disconnect()


@pytest.mark.asyncio
async def test_get_state():
    async with ClientSession() as session:
        client = StreamMagicClient(DEVICE_HOST, session=session)
        await client.connect()
        state = client.state
        assert state is not None
        await client.disconnect()


@pytest.mark.asyncio
async def test_set_and_restore_volume_limit():
    async with ClientSession() as session:
        client = StreamMagicClient(DEVICE_HOST, session=session)
        await client.connect()
        # TODO: Find out how to get current limit for older versions
        if Version(client.info.api_version) >= Version("1.9"):
            # Get the current volume limit
            audio = client.audio
            assert audio is not None
            old_limit = audio.volume_limit_percent

            # Set a new value
            new_limit = 55 if old_limit != 55 else 60
            await client.set_volume_limit(new_limit)

            # Fetch again to verify
            audio = await client.get_audio()
            assert audio is not None
            assert audio.volume_limit_percent == new_limit

            # Restore old value
            await client.set_volume_limit(old_limit)

        await client.disconnect()
