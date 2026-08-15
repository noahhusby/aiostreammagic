"""Tests for connecting, state population, subscriptions and teardown."""

import pytest
from aiohttp import ClientSession
from aiohttp.test_utils import TestServer
from conftest import ConnectClient
from fake_device import FakeStreamMagicDevice, create_app, wait_until

from aiostreammagic import endpoints as ep
from aiostreammagic.exceptions import StreamMagicError
from aiostreammagic.models import (
    CallbackType,
    ControlBusMode,
    DisplayBrightness,
    TransportControl,
)
from aiostreammagic.stream_magic import StreamMagicClient


async def test_connect_populates_info(client: StreamMagicClient) -> None:
    assert client.info.model == "CXN100"
    assert client.info.api_version == "1.9"
    assert client.info.timezone == "Europe/Berlin"


async def test_connect_populates_sources(client: StreamMagicClient) -> None:
    assert [source.id for source in client.sources][:1] == ["IR"]
    assert all(source.name for source in client.sources)


async def test_connect_populates_state(client: StreamMagicClient) -> None:
    assert client.state.source == "TIDAL"
    assert client.state.power is True
    assert client.state.volume_percent == 100
    assert client.state.control_bus == ControlBusMode.AMPLIFIER


async def test_connect_populates_audio(client: StreamMagicClient) -> None:
    assert client.audio.volume_limit_percent == 100
    assert client.audio.balance == 0
    assert client.audio.user_eq is not None
    assert len(client.audio.user_eq.bands) == 7
    assert client.audio.tilt_eq is not None


async def test_connect_populates_play_state(client: StreamMagicClient) -> None:
    assert client.play_state.state == "play"
    assert client.play_state.metadata.artist == "Test Artist"
    assert client.play_state.metadata.title == "Test Track"
    assert TransportControl.PLAY_PAUSE in client.now_playing.controls
    assert TransportControl.TOGGLE_SHUFFLE in client.now_playing.controls


async def test_connect_populates_remaining_endpoints(
    client: StreamMagicClient,
) -> None:
    assert client.display.brightness == DisplayBrightness.DIM
    assert client.update.update_available is False
    assert [preset.preset_id for preset in client.preset_list.presets] == [1, 2, 3]
    assert client.preset_list.presets[0].name == "Test Radio One"
    # The CXN100 reports no switchable outputs.
    assert client.audio_output.outputs == []


async def test_connect_subscribes_to_state_endpoints(
    client: StreamMagicClient, device: FakeStreamMagicDevice
) -> None:
    assert device.subscriptions >= {
        ep.INFO,
        ep.SOURCES,
        ep.ZONE_STATE,
        ep.PLAY_STATE,
        ep.POSITION,
        ep.NOW_PLAYING,
        ep.ZONE_AUDIO_OUTPUT,
        ep.DISPLAY,
        ep.UPDATE,
        ep.PRESET_LIST,
        ep.AUDIO,
    }


async def test_disconnect_marks_client_disconnected(
    client: StreamMagicClient,
) -> None:
    assert client.is_connected()

    await client.disconnect()

    assert not client.is_connected()


async def test_commands_fail_after_disconnect(client: StreamMagicClient) -> None:
    await client.disconnect()

    with pytest.raises(StreamMagicError, match="Not connected"):
        await client.set_volume(10)


async def test_caller_provided_session_is_left_open(
    device: FakeStreamMagicDevice,
) -> None:
    async with TestServer(create_app(device)) as server, ClientSession() as session:
        client = StreamMagicClient(
            f"{server.host}:{server.port}",
            session=session,
            should_close_session=False,
        )
        await client.connect()
        await client.disconnect()

        assert not session.closed


async def test_unsolicited_emit_updates_state_and_callbacks(
    client: StreamMagicClient, device: FakeStreamMagicDevice
) -> None:
    callbacks: list[CallbackType] = []

    async def on_update(_: StreamMagicClient, callback_type: CallbackType) -> None:
        callbacks.append(callback_type)

    await client.register_state_update_callbacks(on_update)
    device.data(ep.ZONE_STATE)["volume_percent"] = 33
    await device.emit(ep.ZONE_STATE)

    await wait_until(lambda: client.state.volume_percent == 33)
    assert CallbackType.STATE in callbacks


async def test_error_response_raises_stream_magic_error(
    client: StreamMagicClient, device: FakeStreamMagicDevice
) -> None:
    device.fail(ep.ZONE_STATE, result=400, message="Bad request")

    with pytest.raises(StreamMagicError, match="Bad request"):
        await client.set_volume(50)


async def test_older_api_device_connects(connect_client: ConnectClient) -> None:
    client = await connect_client(FakeStreamMagicDevice(model="851n"))

    assert client.info.api_version == "1.8"
    assert client.state.volume_percent == 40
