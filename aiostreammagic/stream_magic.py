"""Asynchronous Python client for StreamMagic API."""
import asyncio
import socket
from dataclasses import dataclass
from typing import Any

from aiohttp import ClientSession, ClientError, ClientResponseError
from aiohttp.hdrs import METH_GET
from yarl import URL

from aiostreammagic.exceptions import StreamMagicError, StreamMagicConnectionError
from aiostreammagic.models import Info, Source, State, PlayState

VERSION = '1.0.0'


@dataclass
class StreamMagicClient:
    """Client for handling connections with StreamMagic enabled devices."""

    host: str
    session: ClientSession | None = None
    request_timeout: int = 10
    _close_session: bool = False

    async def _request(self, url: URL, *, method: str = METH_GET, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a request to a StreamMagic device."""
        headers = {
            "User-Agent": f"aiostreammagic/{VERSION}",
            "Accept": "application/json",
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.request(
                    method,
                    url,
                    headers=headers,
                    json=data,
                )
        except asyncio.TimeoutError as exception:
            msg = "Timeout occurred while connecting to the device"
            raise StreamMagicConnectionError(msg) from exception
        except (
                ClientError,
                ClientResponseError,
                socket.gaierror,
        ) as exception:
            msg = "Error occurred while communicating with the device"
            raise StreamMagicConnectionError(msg) from exception

        if response.status != 200:
            content_type = response.headers.get("Content-Type", "")
            text = await response.text()
            msg = "Unexpected response from "
            raise StreamMagicConnectionError(
                msg,
                {"Content-Type": content_type, "response": text},
            )

        return await response.json()

    async def _request_device(self, uri: str, *, query: str = ""):
        url = URL.build(scheme="http", host=self.host, path=f"/smoip/{uri}", query=query)
        print(url)
        return await self._request(url, method="GET")

    async def get_info(self) -> Info:
        """Get device information from device."""
        data = await self._request_device('system/info')
        return Info.from_dict(data["data"])

    async def get_sources(self) -> list[Source]:
        """Get source information from device."""
        data = await self._request_device('system/sources')
        sources = [Source.from_dict(x) for x in data["data"]["sources"]]
        return sources

    async def get_state(self) -> State:
        """Get state information from device."""
        data = await self._request_device('zone/state')
        return State.from_dict(data["data"])

    async def get_play_state(self) -> PlayState:
        """Get play state information from device."""
        data = await self._request_device('zone/play_state')
        return PlayState.from_dict(data["data"])

    async def power_on(self) -> None:
        """Set the power of the device to on."""
        await self._request_device('system/power', query='power=ON')

    async def power_off(self) -> None:
        """Set the power of the device to network."""
        await self._request_device('system/power', query='power=NETWORK')

    async def volume_up(self) -> None:
        """Increase the volume of the device by 1."""
        await self._request_device('zone/state', query='zone=ZONE1&volume_step_change=1')

    async def volume_down(self) -> None:
        """Increase the volume of the device by -1."""
        await self._request_device('zone/state', query='zone=ZONE1&volume_step_change=-1')

    async def set_volume(self, volume: int) -> None:
        """Set the volume of the device."""
        if not 0 <= volume <= 100:
            raise StreamMagicError("Volume must be between 0 and 100")
        await self._request_device('zone/state', query=f"zone=ZONE1&volume_percent={str(volume)}")

    async def mute(self) -> None:
        """Mute the device."""
        await self._request_device('zone/state', query='zone=ZONE1&mute=true')

    async def unmute(self) -> None:
        """Unmute the device."""
        await self._request_device('zone/state', query='zone=ZONE1&mute=false')

    async def set_source(self, source: Source) -> None:
        """Set the source of the device."""
        await self.set_source_by_id(source.id)

    async def set_source_by_id(self, source_id: str) -> None:
        """Set the source of the device."""
        await self._request_device('zone/state', query=f"zone=ZONE1&source={source_id}")

    async def media_seek(self, position: int) -> None:
        """Set the media position of the device."""
        await self._request_device('zone/play_control', query=f"position={position}")

    async def next_track(self) -> None:
        """Skip the next track."""
        await self._request_device('zone/play_control', query='skip_track=1')

    async def previous_track(self) -> None:
        """Skip the next track."""
        await self._request_device('zone/play_control', query='skip_track=-1')

    async def play_pause(self) -> None:
        """Toggle play/pause."""
        await self._request_device('zone/play_control', query='action=toggle')

    async def pause(self) -> None:
        """Pause the device."""
        await self._request_device('zone/play_control', query='action=pause')

    async def stop(self) -> None:
        """Pause the device."""
        await self._request_device('zone/play_control', query='action=stop')

    async def set_shuffle(self, shuffle: str):
        """Set the shuffle of the device."""
        await self._request_device('zone/play_control', query=f"mode_shuffle={shuffle}")

    async def set_repeat(self, repeat: str):
        """Set the repeat of the device."""
        await self._request_device('zone/play_control', query=f"mode_repeat={repeat}")
