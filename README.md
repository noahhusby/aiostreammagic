<div align="center">

# aiostreammagic

#### An async python package for interfacing with Cambridge Audio / Stream Magic compatible streamers

[**📖 Read the docs »**][docs]

[![GitHub Release][releases-shield]][releases]
[![Python Versions][python-versions-shield]][pypi]
[![Downloads][downloads-shield]][pypi]
![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE.md)

</div>

# About
This module implements a Python client for the Stream Magic API used to control Cambridge Audio streamers. The API connects over websockets and supports several streamers, receivers, and pre-amps.

## Supported Devices
- Cambridge Audio Evo 75
- Cambridge Audio Evo 150
- Cambridge Audio CXN
- Cambridge Audio CXN (v2)
- Cambridge Audio CXR120
- Cambridge Audio CXR200
- Cambridge Audio 851N
- Cambridge Audio Edge NQ

If your model is not on the list of supported devices, and everything works correctly then add it to the list by opening a pull request.

# Installation
```shell
pip install aiostreammagic
```

# Examples

## Basic Example
```python
import asyncio

from aiostreammagic import StreamMagicClient, Source, Info

HOST = "192.168.20.218"


async def main():
    """Basic demo entrypoint."""
    client = StreamMagicClient("192.168.20.218")
    await client.connect()

    info: Info = await client.get_info()
    sources: list[Source] = await client.get_sources()

    print(f"Model: {info.model}")
    for source in sources:
        print(f"Name: {source.id} ({source.id})")

    await client.disconnect()

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
    print(f"System info: {client.get_info()}")
    print(f"Sources: {client.get_sources()}")
    print(f"State: {client.get_state()}")
    print(f"Play State: {client.get_play_state()}")
    print(f"Now Playing: {client.get_now_playing()}")

async def main():
    """Subscribe demo entrypoint."""
    client = StreamMagicClient("192.168.20.218")
    await client.register_state_update_callbacks(on_state_change)
    await client.connect()

    # Play media using the unit's front controls or StreamMagic app
    await asyncio.sleep(60)

    await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
```

[license-shield]: https://img.shields.io/github/license/noahhusby/aiostreammagic.svg
[docs]: https://noahhusby.github.io/aiostreammagic/
[downloads-shield]: https://img.shields.io/pypi/dm/aiostreammagic
[python-versions-shield]: https://img.shields.io/pypi/pyversions/aiostreammagic
[maintenance-shield]: https://img.shields.io/maintenance/yes/2024.svg
[releases-shield]: https://img.shields.io/github/release/noahhusby/aiostreammagic.svg
[releases]: https://github.com/noahhusby/aiostreammagic/releases
[pypi]: https://pypi.org/project/aiostreammagic/
