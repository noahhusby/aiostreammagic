"""Tests for transport controls, queue modes, presets and radio playback."""

import pytest

from aiostreammagic import endpoints as ep
from aiostreammagic.models import RepeatMode, ShuffleMode
from aiostreammagic.stream_magic import StreamMagicClient
from fake_device import FakeStreamMagicDevice, wait_until


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


async def test_recall_preset(
    client: StreamMagicClient, device: FakeStreamMagicDevice
) -> None:
    await client.recall_preset(3)

    assert device.recalled_presets == [3]
    assert device.requests_for(ep.RECALL_PRESET)[-1]["zone"] == "ZONE1"


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
