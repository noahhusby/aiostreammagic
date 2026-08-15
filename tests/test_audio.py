"""Tests for audio settings: volume limit, balance, equalizer and room correction."""

import pytest

from aiostreammagic.exceptions import StreamMagicError
from aiostreammagic.models import EQBand, EQFilterType
from aiostreammagic.stream_magic import StreamMagicClient
from conftest import ConnectClient
from fake_device import FakeStreamMagicDevice, wait_until


def _band(client: StreamMagicClient, index: int) -> EQBand:
    assert client.audio.user_eq is not None
    return client.audio.user_eq.bands[index]


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
