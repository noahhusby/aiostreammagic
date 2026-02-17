<div align="center">

# aiostreammagic

#### An async python package for interfacing with Cambridge Audio / Stream Magic compatible streamers

[**📖 Read the docs »**][docs]

[![GitHub Release][releases-shield]][releases]
[![Python Versions][python-versions-shield]][pypi]
[![License][license-shield]](LICENSE.md)

</div>

# About

This module implements a Python client for the Stream Magic API used to control Cambridge Audio streamers. The API connects over websockets and supports several streamers, receivers, and pre-amps.

## Supported Devices

- Cambridge Audio Evo One
- Cambridge Audio Evo 75
- Cambridge Audio Evo 150
- Cambridge Audio CXN
- Cambridge Audio CXN V2
- Cambridge Audio CXN100
- Cambridge Audio CXR120
- Cambridge Audio CXR200
- Cambridge Audio 851N
- Cambridge Audio Edge NQ
- Cambridge Audio AXN10

If your model is not on the list of supported devices, and everything works correctly then add it to the list by opening a pull request.

# Installation

```shell
pip install aiostreammagic
```

# Usage

## Basic Example

```python
import asyncio

from aiostreammagic import StreamMagicClient

HOST = "192.168.20.218"


async def main():
    """Basic demo entrypoint."""
    async with StreamMagicClient(HOST) as client:

        print(f"Model: {client.info.model}")

        for source in client.sources:
            print(f"Name: {source.id} ({source.id})")

if __name__ == '__main__':
    asyncio.run(main())
```

## Subscription Example

The Cambridge Audio StreamMagic API can automatically notify the client of changes instead of the need for polling. Register a callback to be called whenver new information is available.

```python
import asyncio

from aiostreammagic import StreamMagicClient

HOST = "192.168.20.218"


async def on_state_change(client: StreamMagicClient):
    """Called when new information is received."""
    print(f"System info: {client.info}")
    print(f"Sources: {client.sources}")
    print(f"State: {client.state}")
    print(f"Play State: {client.play_state}")
    print(f"Now Playing: {client.now_playing}")

async def main():
    """Subscribe demo entrypoint."""
    client = StreamMagicClient(HOST)
    await client.register_state_update_callbacks(on_state_change)
    await client.connect()

    # Play media using the unit's front controls or StreamMagic app
    await asyncio.sleep(60)

    await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
```

## Advanced Audio Settings

### Balance

Adjust left/right speaker balance (requires pre-amp mode):

```python
async with StreamMagicClient(HOST) as client:
    await client.set_pre_amp_mode(True)
    await client.set_balance(-5)  # Range: -15 (left) to 15 (right)
```

### Room Correction

Enable and adjust tilt EQ for room acoustics (negative values add warmth for bright/hard-surfaced rooms, positive values add brightness for soft/damped rooms):

```python
async with StreamMagicClient(HOST) as client:
    await client.set_room_correction_mode(True)
    await client.set_room_correction_intensity(8)  # Range: -15 to 15
```

### Equalizer

Configure the 7-band parametric equalizer (bands 0-6 at 80, 120, 315, 800, 2000, 5000, 8000 Hz):

```python
from aiostreammagic import EQBand, UserEQ

async with StreamMagicClient(HOST) as client:
    # Enable equalizer
    await client.set_equalizer_mode(True)

    # Adjust individual bands (0-6)
    await client.set_equalizer_band_gain(3, 2.5)  # Band 3, +2.5 dB, Range: -6 to +3

    # Set all bands at once (Balanced Hi-Fi preset)
    gains = [1.0, 0.5, 0.0, 0.0, 0.0, 0.5, 1.0]
    bands = [EQBand(index=i, gain=gains[i]) for i in range(7)]
    await client.set_equalizer_params(bands)

    # Reset to defaults
    await client.set_equalizer_defaults()
```

[license-shield]: https://img.shields.io/github/license/noahhusby/aiostreammagic.svg
[docs]: https://noahhusby.github.io/aiostreammagic/
[python-versions-shield]: https://img.shields.io/pypi/pyversions/aiostreammagic
[releases-shield]: https://img.shields.io/github/release/noahhusby/aiostreammagic.svg
[releases]: https://github.com/noahhusby/aiostreammagic/releases
[pypi]: https://pypi.org/project/aiostreammagic/
