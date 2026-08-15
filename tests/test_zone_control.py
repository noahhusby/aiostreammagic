"""Tests for zone-level controls: volume, source, power and device settings."""

import pytest
from fake_device import FakeStreamMagicDevice, wait_until

from aiostreammagic import endpoints as ep
from aiostreammagic.exceptions import StreamMagicError
from aiostreammagic.models import ControlBusMode, DisplayBrightness, StandbyMode
from aiostreammagic.stream_magic import StreamMagicClient


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


@pytest.mark.parametrize(
    "brightness",
    [DisplayBrightness.DIM, DisplayBrightness.BRIGHT],
)
async def test_set_display_brightness(
    client: StreamMagicClient, brightness: DisplayBrightness
) -> None:
    await client.set_display_brightness(DisplayBrightness.OFF)
    await wait_until(lambda: client.display.brightness == DisplayBrightness.OFF.value)

    await client.set_display_brightness(brightness)
    await wait_until(lambda: client.display.brightness == brightness.value)


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
