"""Asynchronous Python client for StreamMagic API."""

import asyncio
import json
from asyncio import AbstractEventLoop, Future, Task, Queue
from datetime import datetime, UTC
from typing import Any, Optional

from aiohttp import ClientWebSocketResponse, ClientSession

from aiostreammagic.exceptions import StreamMagicError
from aiostreammagic.models import (
    Info,
    Source,
    State,
    PlayState,
    NowPlaying,
    ShuffleMode,
    RepeatMode,
    CallbackType,
    AudioOutput,
    Display,
    DisplayBrightness,
    Update,
    PresetList,
)
from . import endpoints as ep
from .const import _LOGGER

VERSION = "1.0.0"


class StreamMagicClient:
    """Client for handling connections with StreamMagic enabled devices."""

    def __init__(self, host: str, session: ClientSession | None = None) -> None:
        self.host = host
        self.session: Optional[ClientSession] = session
        self.connection: ClientWebSocketResponse | None = None
        self.futures: dict[str, list[Future[Any]]] = {}
        self._subscriptions: dict[str, Any] = {}
        self._loop: AbstractEventLoop = asyncio.get_running_loop()
        self.connect_result: Future[bool] | None = None
        self.connect_task: Task[Any] | None = None
        self.state_update_callbacks: list[Any] = []
        self._allow_state_update = False
        self._info: Optional[Info] = None
        self.sources: list[Source] = []
        self._state: Optional[State] = None
        self._play_state: Optional[PlayState] = None
        self._now_playing: Optional[NowPlaying] = None
        self._audio_output: Optional[AudioOutput] = None
        self._display: Optional[Display] = None
        self._update: Optional[Update] = None
        self._preset_list: Optional[PresetList] = None
        self._attempt_reconnection = False
        self._reconnect_task: Optional[Task[Any]] = None
        self.position_last_updated: datetime = datetime.now()

    async def register_state_update_callbacks(self, callback: Any) -> None:
        """Register state update callback."""
        self.state_update_callbacks.append(callback)
        if self._allow_state_update:
            await callback(self, CallbackType.STATE)

    def unregister_state_update_callbacks(self, callback: Any) -> None:
        """Unregister state update callback."""
        if callback in self.state_update_callbacks:
            self.state_update_callbacks.remove(callback)

    def clear_state_update_callbacks(self) -> None:
        """Clear state update callbacks."""
        self.state_update_callbacks.clear()

    async def do_state_update_callbacks(
        self, callback_type: CallbackType = CallbackType.STATE
    ) -> None:
        """Call state update callbacks."""
        if not self.state_update_callbacks:
            return
        callbacks = set()
        for callback in self.state_update_callbacks:
            callbacks.add(callback(self, callback_type))

        if callbacks:
            await asyncio.gather(*callbacks)

    async def connect(self) -> Any:
        """Connect to StreamMagic enabled devices."""
        if not self.is_connected():
            self.connect_result = self._loop.create_future()
            self._reconnect_task = asyncio.create_task(
                self._reconnect_handler(self.connect_result)
            )
        return await self.connect_result

    async def disconnect(self) -> None:
        """Disconnect from StreamMagic enabled devices."""
        if self.is_connected():
            self._attempt_reconnection = False
            self.connect_task.cancel()
            try:
                await self.connect_task
            except asyncio.CancelledError:
                pass
            await self.do_state_update_callbacks(CallbackType.CONNECTION)

    def is_connected(self) -> bool:
        """Return True if device is connected."""
        return self.connect_task is not None and not self.connect_task.done()

    async def _ws_connect(self, uri: str) -> ClientWebSocketResponse:
        """Establish a connection with a WebSocket."""
        return await self.session.ws_connect(
            uri,
            headers={
                "Origin": f"ws://{self.host}",
                "Host": f"{self.host}:80",
            },
        )

    async def _reconnect_handler(self, res: Future[bool]) -> None:
        reconnect_delay = 0.5
        while True:
            try:
                self.connect_task = asyncio.create_task(self._connect_handler(res))
                await self.connect_task
            except Exception as ex:
                _LOGGER.error(ex)
                pass
            await self.do_state_update_callbacks(CallbackType.CONNECTION)
            if not self._attempt_reconnection:
                _LOGGER.debug(
                    "Failed to connect to device on initial pass, skipping reconnect."
                )
                break
            reconnect_delay = min(reconnect_delay * 2, 30)
            _LOGGER.debug(
                f"Attempting reconnection to Cambridge Audio device in {reconnect_delay} seconds..."
            )
            await asyncio.sleep(reconnect_delay)

    async def _connect_handler(self, res: Future[bool]) -> None:
        """Handle connection for StreamMagic."""
        try:
            if not self.session:
                self.session = ClientSession()
            self.futures = {}
            self._allow_state_update = False
            uri = f"ws://{self.host}/smoip"
            ws = await self._ws_connect(uri)
            self.connection = ws
            x = asyncio.create_task(
                self.consumer_handler(ws, self._subscriptions, self.futures)
            )
            (
                self._info,
                self.sources,
                self._state,
                self._play_state,
                self._now_playing,
                self._audio_output,
                self._display,
                self._update,
                self._preset_list,
            ) = await asyncio.gather(
                self.get_info(),
                self.get_sources(),
                self.get_state(),
                self.get_play_state(),
                self.get_now_playing(),
                self.get_audio_output(),
                self.get_display(),
                self.get_update(),
                self.get_preset_list(),
            )
            subscribe_state_updates = {
                self.subscribe(self._async_handle_info, ep.INFO),
                self.subscribe(self._async_handle_sources, ep.SOURCES),
                self.subscribe(self._async_handle_zone_state, ep.ZONE_STATE),
                self.subscribe(self._async_handle_play_state, ep.PLAY_STATE),
                self.subscribe(self._async_handle_position, ep.POSITION),
                self.subscribe(self._async_handle_now_playing, ep.NOW_PLAYING),
                self.subscribe(self._async_handle_audio_output, ep.ZONE_AUDIO_OUTPUT),
                self.subscribe(self._async_handle_display, ep.DISPLAY),
                self.subscribe(self._async_handle_update, ep.UPDATE),
                self.subscribe(self._async_handle_preset_list, ep.PRESET_LIST),
            }
            subscribe_tasks = set()
            for state_update in subscribe_state_updates:
                subscribe_tasks.add(asyncio.create_task(state_update))
            await asyncio.wait(subscribe_tasks)
            self._allow_state_update = True
            await self.do_state_update_callbacks(CallbackType.CONNECTION)

            self._attempt_reconnection = True
            if not res.done():
                res.set_result(True)
            await asyncio.wait([x], return_when=asyncio.FIRST_COMPLETED)
        except Exception as ex:
            if not res.done():
                res.set_exception(ex)
            _LOGGER.error(ex, exc_info=True)

    @staticmethod
    async def subscription_handler(queue: Queue, callback) -> None:
        """Handle subscriptions."""
        try:
            while True:
                msg = await queue.get()
                await callback(msg)
        except asyncio.CancelledError:
            pass

    async def consumer_handler(
        self,
        ws: ClientWebSocketResponse,
        subscriptions: dict[str, list[Any]],
        futures: dict[str, list[asyncio.Future]],
    ) -> None:
        """Callback consumer handler."""
        subscription_queues = {}
        subscription_tasks = {}
        try:
            async for raw_msg in ws:
                if futures or subscriptions:
                    _LOGGER.debug("recv(%s): %s", self.host, raw_msg)
                    msg = json.loads(raw_msg.data)
                    path = msg["path"]
                    path_futures = self.futures.get(path)
                    subscription = self._subscriptions.get(path)
                    if path_futures and msg["type"] == "response":
                        for future in path_futures:
                            if not future.done():
                                future.set_result(msg)
                    if subscription:
                        if path not in subscription_tasks:
                            queue = asyncio.Queue()
                            subscription_queues[path] = queue
                            subscription_tasks[path] = asyncio.create_task(
                                self.subscription_handler(queue, subscription)
                            )
                        subscription_queues[path].put_nowait(msg)

        except (asyncio.CancelledError,):
            pass

    async def _send(
        self, path: str, params: Optional[dict[str, str | int | float | bool]] = None
    ) -> None:
        """Send a command to the device."""
        message = {
            "path": path,
            "params": params or {},
        }

        if not self.connection:
            raise StreamMagicError("Not connected to device.")

        _LOGGER.debug("Sending command: %s", message)
        await self.connection.send_str(json.dumps(message))

    async def request(
        self, path: str, params: Optional[dict[str, str | int | float | bool]] = None
    ) -> Any:
        res = self._loop.create_future()
        path_futures = self.futures.get(path, [])
        path_futures.append(res)
        self.futures[path] = path_futures
        try:
            await self._send(path, params)
        except (asyncio.CancelledError, StreamMagicError):
            path_futures.remove(res)
            raise
        try:
            response = await res
        except asyncio.CancelledError:
            if res in path_futures:
                path_futures.remove(res)
            raise
        path_futures.remove(res)
        message = response["message"]
        result = response["result"]
        if result != 200:
            raise StreamMagicError(message)

        return response

    async def subscribe(self, callback: Any, path: str) -> Any:
        self._subscriptions[path] = callback
        try:
            await self._send(path, {"update": 100, "zone": "ZONE1"})
        except (asyncio.CancelledError, StreamMagicError):
            del self._subscriptions[path]
            raise

    @property
    def info(self) -> Info:
        """Return a type-guaranteed instance of Info"""
        if not self._info:
            raise StreamMagicError("Info not available.")
        return self._info

    @property
    def state(self) -> State:
        """Return a type-guaranteed instance of State"""
        if not self._state:
            raise StreamMagicError("State not available.")
        return self._state

    @property
    def play_state(self) -> PlayState:
        """Return a type-guaranteed instance of PlayState"""
        if not self._play_state:
            raise StreamMagicError("Play state not available.")
        return self._play_state

    @property
    def now_playing(self) -> NowPlaying:
        """Return a type-guaranteed instance of NowPlaying"""
        if not self._now_playing:
            raise StreamMagicError("NowPlaying not available.")
        return self._now_playing

    @property
    def audio_output(self) -> AudioOutput:
        """Return a type-guaranteed instance of AudioOutput"""
        if not self._audio_output:
            raise StreamMagicError("AudioOutput not available.")
        return self._audio_output

    @property
    def display(self) -> Display:
        """Return a type-guaranteed instance of Display"""
        if not self._display:
            raise StreamMagicError("Display not available.")
        return self._display

    @property
    def update(self) -> Update:
        """Return a type-guaranteed instance of Update"""
        if not self._update:
            raise StreamMagicError("Update not available.")
        return self._update

    @property
    def preset_list(self) -> PresetList:
        """Return a type-guaranteed instance of PresetList"""
        if not self._preset_list:
            raise StreamMagicError("PresetList not available.")
        return self._preset_list

    async def get_info(self) -> Info:
        """Get device information from device."""
        data = await self.request(ep.INFO)
        return Info.from_dict(data["params"]["data"])

    async def get_sources(self) -> list[Source]:
        """Get source information from device."""
        data = await self.request(ep.SOURCES)
        sources = [Source.from_dict(x) for x in data["params"]["data"]["sources"]]
        return sources

    async def get_state(self) -> State:
        """Get state information from device."""
        data = await self.request(ep.ZONE_STATE)
        return State.from_dict(data["params"]["data"])

    async def get_play_state(self) -> PlayState:
        """Get play state information from device."""
        data = await self.request(ep.PLAY_STATE)
        return PlayState.from_dict(data["params"]["data"])

    async def get_now_playing(self) -> NowPlaying:
        """Get now playing information from device."""
        data = await self.request(ep.NOW_PLAYING)
        return NowPlaying.from_dict(data["params"]["data"])

    async def get_audio_output(self) -> AudioOutput:
        """Get audio output information from device."""
        data = await self.request(ep.ZONE_AUDIO_OUTPUT)
        return AudioOutput.from_dict(data["params"]["data"])

    async def get_display(self) -> Display:
        """Get display information from device."""
        data = await self.request(ep.DISPLAY)
        return Display.from_dict(data["params"]["data"])

    async def get_update(self) -> Update:
        """Get display information from device."""
        data = await self.request(ep.UPDATE)
        return Update.from_dict(data["params"]["data"])

    async def get_preset_list(self) -> PresetList:
        """Get preset list information from device."""
        data = await self.request(ep.PRESET_LIST)
        return PresetList.from_dict(data["params"]["data"])

    async def _async_handle_info(self, payload: dict[str, Any]) -> None:
        """Handle async info update."""
        params = payload["params"]
        if "data" in params:
            self._info = Info.from_dict(params["data"])
        await self.do_state_update_callbacks()

    async def _async_handle_sources(self, payload: dict[str, Any]) -> None:
        """Handle async sources update."""
        params = payload["params"]
        if "data" in params:
            self.sources = [Source.from_dict(x) for x in params["data"]["sources"]]
        await self.do_state_update_callbacks()

    async def _async_handle_zone_state(self, payload: dict[str, Any]) -> None:
        """Handle async zone state update."""
        params = payload["params"]
        if "data" in params:
            self._state = State.from_dict(params["data"])
        await self.do_state_update_callbacks()

    async def _async_handle_play_state(self, payload: dict[str, Any]) -> None:
        """Handle async zone state update."""
        params = payload["params"]
        if "data" in params:
            self._play_state = PlayState.from_dict(params["data"])
            self.position_last_updated = datetime.now()
        await self.do_state_update_callbacks()

    async def _async_handle_position(self, payload: dict[str, Any]) -> None:
        """Handle async position update."""
        params = payload["params"]
        if "data" in params and params["data"]["position"] and self.play_state:
            self.play_state.position = params["data"]["position"]
            self.position_last_updated = datetime.now(UTC)
        await self.do_state_update_callbacks()

    async def _async_handle_now_playing(self, payload: dict[str, Any]) -> None:
        """Handle async now playing update."""
        params = payload["params"]
        if "data" in params:
            self._now_playing = NowPlaying.from_dict(params["data"])
        await self.do_state_update_callbacks()

    async def _async_handle_audio_output(self, payload: dict[str, Any]) -> None:
        """Handle async audio output update."""
        params = payload["params"]
        if "data" in params:
            self._audio_output = AudioOutput.from_dict(params["data"])
        await self.do_state_update_callbacks()

    async def _async_handle_display(self, payload: dict[str, Any]) -> None:
        """Handle async display update."""
        params = payload["params"]
        if "data" in params:
            self._display = Display.from_dict(params["data"])
        await self.do_state_update_callbacks()

    async def _async_handle_update(self, payload: dict[str, Any]) -> None:
        """Handle async display update."""
        params = payload["params"]
        if "data" in params:
            self._update = Update.from_dict(params["data"])
        await self.do_state_update_callbacks()

    async def _async_handle_preset_list(self, payload: dict[str, Any]) -> None:
        """Handle async preset list update."""
        params = payload["params"]
        if "data" in params:
            self._preset_list = PresetList.from_dict(params["data"])
        await self.do_state_update_callbacks()

    async def power_on(self) -> None:
        """Set the power of the device to on."""
        await self.request(ep.POWER, params={"power": "ON"})

    async def power_off(self) -> None:
        """Set the power of the device to network."""
        await self.request(ep.POWER, params={"power": "NETWORK"})

    async def volume_up(self) -> None:
        """Increase the volume of the device by 1."""
        await self.request(
            ep.ZONE_STATE, params={"zone": "ZONE1", "volume_step_change": 1}
        )

    async def volume_down(self) -> None:
        """Increase the volume of the device by -1."""
        await self.request(
            ep.ZONE_STATE, params={"zone": "ZONE1", "volume_step_change": -1}
        )

    async def set_volume(self, volume: int) -> None:
        """Set the volume of the device."""
        if not 0 <= volume <= 100:
            raise StreamMagicError("Volume must be between 0 and 100")
        await self.request(
            ep.ZONE_STATE, params={"zone": "ZONE1", "volume_percent": volume}
        )

    async def set_mute(self, mute: bool) -> None:
        """Set the mute of the device."""
        await self.request(ep.ZONE_STATE, params={"zone": "ZONE1", "mute": mute})

    async def set_source(self, source: Source) -> None:
        """Set the source of the device."""
        await self.set_source_by_id(source.id)

    async def set_source_by_id(self, source_id: str) -> None:
        """Set the source of the device."""
        await self.request(ep.ZONE_STATE, params={"zone": "ZONE1", "source": source_id})

    async def media_seek(self, position: int) -> None:
        """Set the media position of the device."""
        await self.request(
            ep.PLAY_CONTROL, params={"zone": "ZONE1", "position": position}
        )

    async def next_track(self) -> None:
        """Skip the next track."""
        await self.request(
            ep.PLAY_CONTROL, params={"match": "none", "zone": "ZONE1", "skip_track": 1}
        )

    async def previous_track(self) -> None:
        """Skip the next track."""
        await self.request(
            ep.PLAY_CONTROL, params={"match": "none", "zone": "ZONE1", "skip_track": -1}
        )

    async def play_pause(self) -> None:
        """Toggle play/pause."""
        await self.request(
            ep.PLAY_CONTROL,
            params={"match": "none", "zone": "ZONE1", "action": "toggle"},
        )

    async def play(self) -> None:
        """Play the device."""
        await self.request(
            ep.PLAY_CONTROL,
            params={"match": "none", "zone": "ZONE1", "action": "play"},
        )

    async def pause(self) -> None:
        """Pause the device."""
        await self.request(
            ep.PLAY_CONTROL,
            params={"match": "none", "zone": "ZONE1", "action": "pause"},
        )

    async def stop(self) -> None:
        """Pause the device."""
        await self.request(
            ep.PLAY_CONTROL, params={"match": "none", "zone": "ZONE1", "action": "stop"}
        )

    async def set_shuffle(self, shuffle: ShuffleMode) -> None:
        """Set the shuffle of the device."""
        await self.request(
            ep.PLAY_CONTROL,
            params={"match": "none", "zone": "ZONE1", "mode_shuffle": shuffle},
        )

    async def set_repeat(self, repeat: RepeatMode) -> None:
        """Set the repeat of the device."""
        await self.request(
            ep.PLAY_CONTROL,
            params={"match": "none", "zone": "ZONE1", "mode_repeat": repeat},
        )

    async def play_radio_airable(self, name: str, airable_radio_id: int) -> None:
        """Play an airable radio station."""
        await self.request(
            ep.STREAM_RADIO,
            params={
                "zone": "ZONE1",
                "airable_radio_id": airable_radio_id,
                "name": name,
            },
        )

    async def play_radio_url(self, name: str, url: str) -> None:
        """Play a radio station from a provided url."""
        await self.request(
            ep.STREAM_RADIO, params={"zone": "ZONE1", "url": url, "name": name}
        )

    async def set_audio_output(self, output_id: str) -> None:
        """Set the audio output of the device."""
        await self.request(
            ep.ZONE_AUDIO_OUTPUT, params={"zone": "ZONE1", "id": output_id}
        )

    async def set_pre_amp_mode(self, enabled: bool) -> None:
        """Sets whether the internal pre-amp is enabled."""
        await self.request(ep.ZONE_STATE, params={"pre_amp_mode": enabled})

    async def set_volume_limit(self, volume_limit_percent: int) -> None:
        """Sets the volume limit for the internal pre-amp. Value must be between 0 and 100."""
        if not 0 <= volume_limit_percent <= 100:
            raise StreamMagicError("Volume limit must be between 0 and 100")
        await self.request(
            ep.ZONE_STATE, params={"volume_limit_percent": volume_limit_percent}
        )

    async def set_device_name(self, device_name: str) -> None:
        """Set the device name."""
        await self.request(ep.INFO, params={"name": device_name})

    async def set_display_brightness(
        self, display_brightness: DisplayBrightness
    ) -> None:
        """Set the display brightness of the device."""
        await self.request(ep.DISPLAY, params={"brightness": display_brightness})

    async def set_early_update(self, early_update: bool) -> None:
        """Set whether the device should be on the early update channel."""
        await self.request(
            ep.UPDATE, params={"early_update": early_update, "action": "CHECK"}
        )

    async def recall_preset(self, preset: int) -> None:
        """Recall a preset for the device."""
        await self.request(ep.RECALL_PRESET, params={"preset": preset, "zone": "ZONE1"})
