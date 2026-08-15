"""Unit tests for `StreamMagicClient` against an in-memory fake device."""

import pytest
from aiohttp import ClientSession
from aiohttp.test_utils import TestServer

from aiostreammagic import endpoints as ep
from aiostreammagic.exceptions import StreamMagicError
from aiostreammagic.models import (
    CallbackType,
    ControlBusMode,
    DisplayBrightness,
    EQBand,
    EQFilterType,
    RepeatMode,
    ShuffleMode,
    StandbyMode,
    TransportControl,
)
from aiostreammagic.stream_magic import StreamMagicClient
from conftest import ConnectClient
from fake_device import FakeStreamMagicDevice, create_app, wait_until


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


@pytest.mark.parametrize("volume", [0, 25, 50, 100])
async def test_set_volume(client: StreamMagicClient, volume: int) -> None:
    await client.set_volume(volume)

    await wait_until(lambda: client.state.volume_percent == volume)


@pytest.mark.parametrize("volume", [-1, 101])
async def test_set_volume_rejects_out_of_range(
    client: StreamMagicClient, device: FakeStreamMagicDevice, volume: int
) -> None:
    sent = len(device.requests)

    with pytest.raises(StreamMagicError, match="between 0 and 100"):
        await client.set_volume(volume)

    assert len(device.requests) == sent


async def test_volume_up_and_down(
    client: StreamMagicClient, device: FakeStreamMagicDevice
) -> None:
    device.data(ep.ZONE_STATE)["volume_percent"] = 50

    await client.volume_up()
    await wait_until(lambda: client.state.volume_percent == 51)

    await client.volume_down()
    await wait_until(lambda: client.state.volume_percent == 50)


@pytest.mark.parametrize("mute", [True, False])
async def test_set_mute(client: StreamMagicClient, mute: bool) -> None:
    await client.set_mute(mute)

    await wait_until(lambda: client.state.mute == mute)


async def test_set_source_by_id(client: StreamMagicClient) -> None:
    await client.set_source_by_id("SPOTIFY")

    await wait_until(lambda: client.state.source == "SPOTIFY")


async def test_set_source_uses_source_id(client: StreamMagicClient) -> None:
    source = client.sources[0]

    await client.set_source(source)

    await wait_until(lambda: client.state.source == source.id)


@pytest.mark.parametrize("enabled", [True, False])
async def test_set_pre_amp_mode(client: StreamMagicClient, enabled: bool) -> None:
    await client.set_pre_amp_mode(enabled)

    await wait_until(lambda: client.state.pre_amp_mode == enabled)


async def test_power_on(client: StreamMagicClient) -> None:
    await client.power_on()

    await wait_until(lambda: client.state.power is True)


async def test_power_off(client: StreamMagicClient) -> None:
    await client.power_off()

    await wait_until(lambda: client.state.power is False)


async def test_set_standby_mode(client: StreamMagicClient) -> None:
    await client.set_standby_mode(StandbyMode.ECO)

    await wait_until(lambda: client.state.standby_mode == StandbyMode.ECO)


async def test_set_auto_power_down(client: StreamMagicClient) -> None:
    await client.set_auto_power_down(600)

    await wait_until(lambda: client.state.auto_power_down_time == 600)


async def test_set_control_bus_mode(client: StreamMagicClient) -> None:
    await client.set_control_bus_mode(ControlBusMode.RECEIVER)

    await wait_until(lambda: client.state.control_bus == ControlBusMode.RECEIVER)


async def test_set_device_name(client: StreamMagicClient) -> None:
    await client.set_device_name("Living Room")

    await wait_until(lambda: client.info.name == "Living Room")


async def test_set_display_brightness(client: StreamMagicClient) -> None:
    await client.set_display_brightness(DisplayBrightness.DIM)

    await wait_until(lambda: client.display.brightness == DisplayBrightness.DIM)


async def test_set_early_update(client: StreamMagicClient) -> None:
    await client.set_early_update(True)

    await wait_until(lambda: client.update.early_update is True)


async def test_set_audio_output(
    client: StreamMagicClient, device: FakeStreamMagicDevice
) -> None:
    await client.set_audio_output("OUT2")

    assert device.requests_for(ep.ZONE_AUDIO_OUTPUT)[-1] == {
        "zone": "ZONE1",
        "id": "OUT2",
    }


async def test_recall_preset(
    client: StreamMagicClient, device: FakeStreamMagicDevice
) -> None:
    await client.recall_preset(3)

    assert device.recalled_presets == [3]
    assert device.requests_for(ep.RECALL_PRESET)[-1]["zone"] == "ZONE1"


@pytest.mark.parametrize(
    ("method", "action"),
    [("play", "play"), ("pause", "pause"), ("stop", "stop"), ("play_pause", "toggle")],
)
async def test_transport_actions(
    client: StreamMagicClient,
    device: FakeStreamMagicDevice,
    method: str,
    action: str,
) -> None:
    await getattr(client, method)()

    assert device.requests_for(ep.PLAY_CONTROL)[-1]["action"] == action


async def test_track_skipping(
    client: StreamMagicClient, device: FakeStreamMagicDevice
) -> None:
    await client.next_track()
    await client.previous_track()

    assert device.skipped_tracks == [1, -1]


async def test_media_seek(client: StreamMagicClient) -> None:
    await client.media_seek(120)

    await wait_until(lambda: client.play_state.position == 120)


@pytest.mark.parametrize(
    ("mode", "expected"),
    [(ShuffleMode.OFF, "off"), (ShuffleMode.ALL, "all"), (ShuffleMode.TOGGLE, "all")],
)
async def test_set_shuffle(
    client: StreamMagicClient, mode: ShuffleMode, expected: str
) -> None:
    await client.set_shuffle(ShuffleMode.OFF)
    await wait_until(lambda: client.play_state.mode_shuffle == "off")

    await client.set_shuffle(mode)

    await wait_until(lambda: client.play_state.mode_shuffle == expected)


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (RepeatMode.OFF, "off"),
        (RepeatMode.ALL, "all"),
        (RepeatMode.ONE, "one"),
        (RepeatMode.TOGGLE, "all"),
    ],
)
async def test_set_repeat(
    client: StreamMagicClient, mode: RepeatMode, expected: str
) -> None:
    await client.set_repeat(RepeatMode.OFF)
    await wait_until(lambda: client.play_state.mode_repeat == "off")

    await client.set_repeat(mode)

    await wait_until(lambda: client.play_state.mode_repeat == expected)


async def test_play_radio_url(
    client: StreamMagicClient, device: FakeStreamMagicDevice
) -> None:
    await client.play_radio_url("Test Radio", "http://radio.invalid/stream")

    assert device.played_radio == [
        {
            "zone": "ZONE1",
            "url": "http://radio.invalid/stream",
            "name": "Test Radio",
        }
    ]


async def test_play_radio_airable(
    client: StreamMagicClient, device: FakeStreamMagicDevice
) -> None:
    await client.play_radio_airable("Test Radio", 12345)

    assert device.played_radio == [
        {"zone": "ZONE1", "airable_radio_id": 12345, "name": "Test Radio"}
    ]


@pytest.mark.parametrize("limit", [1, 50, 100])
async def test_set_volume_limit(client: StreamMagicClient, limit: int) -> None:
    await client.set_volume_limit(limit)

    await wait_until(lambda: client.audio.volume_limit_percent == limit)


@pytest.mark.parametrize("limit", [0, 101])
async def test_set_volume_limit_rejects_out_of_range(
    client: StreamMagicClient, limit: int
) -> None:
    with pytest.raises(StreamMagicError, match="between 1 and 100"):
        await client.set_volume_limit(limit)


@pytest.mark.parametrize("balance", [-15, -6, 0, 12, 15])
async def test_set_balance(client: StreamMagicClient, balance: int) -> None:
    await client.set_balance(balance)

    await wait_until(lambda: client.audio.balance == balance)


@pytest.mark.parametrize("balance", [-16, 16])
async def test_set_balance_rejects_out_of_range(
    client: StreamMagicClient, balance: int
) -> None:
    with pytest.raises(StreamMagicError, match="between -15 and 15"):
        await client.set_balance(balance)


@pytest.mark.parametrize("enabled", [True, False])
async def test_set_equalizer_mode(client: StreamMagicClient, enabled: bool) -> None:
    await client.set_equalizer_mode(enabled)

    await wait_until(
        lambda: client.audio.user_eq is not None
        and client.audio.user_eq.enabled == enabled
    )


def _band(client: StreamMagicClient, index: int) -> EQBand:
    assert client.audio.user_eq is not None
    return client.audio.user_eq.bands[index]


async def test_set_equalizer_params_updates_bands(client: StreamMagicClient) -> None:
    await client.set_equalizer_params(
        [EQBand(index=1, filter=EQFilterType.NOTCH, freq=200, gain=-1.5, q=2.0)]
    )

    await wait_until(lambda: _band(client, 1).gain == -1.5)
    band = _band(client, 1)
    assert band.filter == EQFilterType.NOTCH
    assert band.freq == 200
    assert band.q == 2.0


async def test_set_equalizer_band_gain_leaves_other_fields(
    client: StreamMagicClient,
) -> None:
    original_freq = _band(client, 2).freq

    await client.set_equalizer_band_gain(2, -3.0)

    await wait_until(lambda: _band(client, 2).gain == -3.0)
    assert _band(client, 2).freq == original_freq


async def test_set_equalizer_band_frequency(client: StreamMagicClient) -> None:
    await client.set_equalizer_band_frequency(3, 1000)

    await wait_until(lambda: _band(client, 3).freq == 1000)


async def test_set_equalizer_band_filter(client: StreamMagicClient) -> None:
    await client.set_equalizer_band_filter(0, EQFilterType.HIGHPASS)

    await wait_until(lambda: _band(client, 0).filter == EQFilterType.HIGHPASS)


async def test_set_equalizer_band_q_factor(client: StreamMagicClient) -> None:
    await client.set_equalizer_band_q_factor(4, 3.5)

    await wait_until(lambda: _band(client, 4).q == 3.5)


@pytest.mark.parametrize("gain", [-6.5, 3.5])
async def test_set_equalizer_band_gain_rejects_out_of_range(
    client: StreamMagicClient, gain: float
) -> None:
    with pytest.raises(StreamMagicError, match="between -6 dB and 3 dB"):
        await client.set_equalizer_band_gain(0, gain)


@pytest.mark.parametrize("frequency", [19, 20001])
async def test_set_equalizer_band_frequency_rejects_out_of_range(
    client: StreamMagicClient, frequency: int
) -> None:
    with pytest.raises(StreamMagicError, match="between 20 Hz and 20 kHz"):
        await client.set_equalizer_band_frequency(0, frequency)


@pytest.mark.parametrize("q_factor", [0.05, 11])
async def test_set_equalizer_band_q_factor_rejects_out_of_range(
    client: StreamMagicClient, q_factor: float
) -> None:
    with pytest.raises(StreamMagicError, match="between 0.1 and 10"):
        await client.set_equalizer_band_q_factor(0, q_factor)


async def test_set_equalizer_preset(client: StreamMagicClient) -> None:
    await client.set_equalizer_preset("bass_boost")

    await wait_until(lambda: _band(client, 0).gain == 3.0)
    assert _band(client, 6).gain == -0.3


async def test_set_equalizer_preset_rejects_unknown_name(
    client: StreamMagicClient,
) -> None:
    with pytest.raises(StreamMagicError, match="Unknown preset"):
        await client.set_equalizer_preset("does_not_exist")


async def test_set_equalizer_defaults(client: StreamMagicClient) -> None:
    await client.set_equalizer_params([EQBand(index=0, gain=2.0)])
    await wait_until(lambda: _band(client, 0).gain == 2.0)

    await client.set_equalizer_defaults()

    await wait_until(lambda: _band(client, 0).gain == 0.0)
    assert _band(client, 0).filter == EQFilterType.LOWSHELF


@pytest.mark.parametrize("enabled", [True, False])
async def test_set_room_correction_mode(
    client: StreamMagicClient, enabled: bool
) -> None:
    await client.set_room_correction_mode(enabled)

    await wait_until(
        lambda: client.audio.tilt_eq is not None
        and client.audio.tilt_eq.enabled == enabled
    )


@pytest.mark.parametrize("intensity", [-15, 0, 15])
async def test_set_room_correction_intensity(
    client: StreamMagicClient, intensity: int
) -> None:
    await client.set_room_correction_intensity(intensity)

    await wait_until(
        lambda: client.audio.tilt_eq is not None
        and client.audio.tilt_eq.intensity == intensity
    )


@pytest.mark.parametrize("intensity", [-16, 16])
async def test_set_room_correction_intensity_rejects_out_of_range(
    client: StreamMagicClient, intensity: int
) -> None:
    with pytest.raises(StreamMagicError, match="between -15 and 15"):
        await client.set_room_correction_intensity(intensity)


async def test_older_api_device_connects(connect_client: ConnectClient) -> None:
    client = await connect_client(FakeStreamMagicDevice(model="851n"))

    assert client.info.api_version == "1.8"
    assert client.state.volume_percent == 40


@pytest.mark.parametrize(
    ("method", "argument", "message"),
    [
        ("set_balance", 0, "Balance is not supported"),
        ("set_equalizer_mode", True, "Equalizer is not supported"),
        ("set_room_correction_mode", True, "Room correction is not supported"),
    ],
)
async def test_audio_features_rejected_when_unsupported(
    connect_client: ConnectClient, method: str, argument: object, message: str
) -> None:
    client = await connect_client(FakeStreamMagicDevice(model="851n"))

    with pytest.raises(StreamMagicError, match=message):
        await getattr(client, method)(argument)
