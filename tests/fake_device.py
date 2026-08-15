"""In-memory fake of a StreamMagic device.

Serves the SMoIP websocket protocol (request/response plus subscription emits)
from mutable state seeded with the captured payloads in ``fixtures/<model>/``,
so tests never talk to a real streamer or change its settings.

Each fixture folder is a capture of one real streamer, not a variant of another:
the 851n runs API 1.8 and genuinely lacks endpoints the cxn100 exposes.
"""

from __future__ import annotations

import asyncio
import copy
import json
from pathlib import Path
from typing import Any, Callable

from aiohttp import WSMsgType, web

from aiostreammagic import endpoints as ep

FIXTURE_DIR = Path(__file__).parent / "fixtures"
DEFAULT_MODEL = "cxn100"

ENDPOINTS: tuple[str, ...] = (
    ep.INFO,
    ep.SOURCES,
    ep.ZONE_STATE,
    ep.PLAY_STATE,
    ep.UPDATE,
    ep.POSITION,
    ep.NOW_PLAYING,
    ep.PLAY_CONTROL,
    ep.STREAM_RADIO,
    ep.POWER,
    ep.AUDIO,
    ep.ZONE_AUDIO_OUTPUT,
    ep.DISPLAY,
    ep.PRESET_LIST,
    ep.RECALL_PRESET,
)

# Every other endpoint either has a capture or parses fine from no data.
# `Display.brightness` is the one required field the 851n capture is missing.
SYNTHETIC_PAYLOADS: dict[str, dict[str, Any]] = {
    ep.DISPLAY: {"data": {"brightness": "bright"}},
}

REPEAT_TOGGLE: dict[str, str] = {"off": "all", "all": "one", "one": "off"}
SHUFFLE_TOGGLE: dict[str, str] = {"off": "all", "all": "off"}
PLAY_ACTION_TOGGLE: dict[str, str] = {"play": "pause", "pause": "play"}


class FakeStreamMagicDevice:
    """Holds device state and turns SMoIP messages into SMoIP replies."""

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self.model = model
        self.payloads: dict[str, dict[str, Any]] = {
            endpoint: self._load_payload(endpoint) for endpoint in ENDPOINTS
        }
        self.requests: list[tuple[str, dict[str, Any]]] = []
        self.subscriptions: set[str] = set()
        self.recalled_presets: list[int] = []
        self.played_radio: list[dict[str, Any]] = []
        self.skipped_tracks: list[int] = []
        self.connections: list[web.WebSocketResponse] = []
        self._failures: dict[str, tuple[int, str]] = {}

    def _load_payload(self, endpoint: str) -> dict[str, Any]:
        """Serve `fixtures/<model>/<endpoint>.json` if captured, else a stub."""
        filename = endpoint.lstrip("/").replace("/", "_") + ".json"
        path = FIXTURE_DIR / self.model / filename
        if path.is_file():
            payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            return payload
        return copy.deepcopy(SYNTHETIC_PAYLOADS.get(endpoint, {"data": {}}))

    def data(self, endpoint: str) -> dict[str, Any]:
        """Return the mutable ``data`` block served for an endpoint."""
        payload = self.payloads.setdefault(endpoint, {"data": {}})
        data: dict[str, Any] = payload.setdefault("data", {})
        return data

    def requests_for(self, path: str) -> list[dict[str, Any]]:
        """Return the params of every request received for a path."""
        return [
            params for request_path, params in self.requests if request_path == path
        ]

    def fail(self, path: str, result: int = 500, message: str = "Device error") -> None:
        """Make the device reject every further request to a path."""
        self._failures[path] = (result, message)

    def handle(self, message: dict[str, Any]) -> list[dict[str, Any]]:
        """Return the messages the device sends back for a client message."""
        path: str = message["path"]
        params: dict[str, Any] = message.get("params") or {}

        if "update" in params:
            self.subscriptions.add(path)
            return [self._message(path, "emit")]

        self.requests.append((path, params))
        failure = self._failures.get(path)
        if failure is not None:
            result, error_message = failure
            return [
                {
                    "path": path,
                    "type": "response",
                    "result": result,
                    "message": error_message,
                    "params": {},
                }
            ]

        changed = self._apply(path, params)
        messages = [self._message(path, "response")]
        messages.extend(
            self._message(changed_path, "emit")
            for changed_path in sorted((changed - {path}) & self.subscriptions)
        )
        return messages

    async def emit(self, path: str) -> None:
        """Push an unsolicited update for a path to every open connection."""
        message = self._message(path, "emit")
        for connection in self.connections:
            if not connection.closed:
                await connection.send_json(message)

    def _message(self, path: str, message_type: str) -> dict[str, Any]:
        return {
            "path": path,
            "type": message_type,
            "result": 200,
            "message": "OK",
            "params": copy.deepcopy(self.payloads.get(path, {"data": {}})),
        }

    def _apply(self, path: str, params: dict[str, Any]) -> set[str]:
        """Mutate device state for a command and report the paths it changed."""
        if path == ep.ZONE_STATE:
            return self._apply_zone_state(params)
        if path == ep.POWER:
            return self._apply_power(params)
        if path == ep.AUDIO:
            return self._apply_audio(params)
        if path == ep.PLAY_CONTROL:
            return self._apply_play_control(params)
        if path == ep.INFO and "name" in params:
            self.data(ep.INFO)["name"] = params["name"]
            return {ep.INFO}
        if path == ep.DISPLAY and "brightness" in params:
            self.data(ep.DISPLAY)["brightness"] = params["brightness"]
            return {ep.DISPLAY}
        if path == ep.UPDATE and "early_update" in params:
            self.data(ep.UPDATE)["early_update"] = params["early_update"]
            return {ep.UPDATE}
        if path == ep.RECALL_PRESET and "preset" in params:
            self.recalled_presets.append(int(params["preset"]))
        if path == ep.STREAM_RADIO and params:
            self.played_radio.append(dict(params))
        return set()

    def _apply_zone_state(self, params: dict[str, Any]) -> set[str]:
        state = self.data(ep.ZONE_STATE)
        for key in ("volume_percent", "mute", "source", "pre_amp_mode", "cbus"):
            if key in params:
                state[key] = params[key]
        if "volume_step_change" in params:
            volume = int(state.get("volume_percent") or 0)
            state["volume_percent"] = max(
                0, min(100, volume + int(params["volume_step_change"]))
            )
        return {ep.ZONE_STATE}

    def _apply_power(self, params: dict[str, Any]) -> set[str]:
        state = self.data(ep.ZONE_STATE)
        if "power" in params:
            state["power"] = params["power"] == "ON"
        for key in ("standby_mode", "auto_power_down"):
            if key in params:
                state[key] = params[key]
        return {ep.ZONE_STATE}

    def _apply_audio(self, params: dict[str, Any]) -> set[str]:
        audio = self.data(ep.AUDIO)
        for key in ("balance", "volume_limit_percent"):
            if key in params:
                audio[key] = params[key]
        if "user_eq" in params:
            audio.setdefault("user_eq", {"bands": []})["enabled"] = params["user_eq"]
        if "user_eq_bands" in params:
            self._apply_eq_bands(audio, params["user_eq_bands"])
        if "tilt_eq" in params:
            audio.setdefault("tilt_eq", {"intensity": 0})["enabled"] = params["tilt_eq"]
        if "tilt_intensity" in params:
            audio.setdefault("tilt_eq", {"enabled": False})["intensity"] = params[
                "tilt_intensity"
            ]
        return {ep.AUDIO}

    @staticmethod
    def _apply_eq_bands(audio: dict[str, Any], raw_bands: str) -> None:
        """Merge an ``index,filter,freq,gain,q|...`` string into the stored bands."""
        user_eq: dict[str, Any] = audio.setdefault("user_eq", {"enabled": False})
        bands: list[dict[str, Any]] = user_eq.setdefault("bands", [])
        by_index = {int(band["index"]): band for band in bands}
        parsers: dict[str, Callable[[str], Any]] = {
            "filter": str,
            "freq": int,
            "gain": float,
            "q": float,
        }
        for chunk in raw_bands.split("|"):
            if not chunk:
                continue
            index_value, *values = chunk.split(",")
            index = int(index_value)
            band = by_index.get(index)
            if band is None:
                band = {"index": index}
                by_index[index] = band
                bands.append(band)
            for key, value in zip(parsers, values):
                if value != "":
                    band[key] = parsers[key](value)
        bands.sort(key=lambda band: int(band["index"]))

    def _apply_play_control(self, params: dict[str, Any]) -> set[str]:
        play_state = self.data(ep.PLAY_STATE)
        if "mode_shuffle" in params:
            mode = str(params["mode_shuffle"])
            current = str(play_state.get("mode_shuffle", "off"))
            play_state["mode_shuffle"] = (
                SHUFFLE_TOGGLE.get(current, "all") if mode == "toggle" else mode
            )
        if "mode_repeat" in params:
            mode = str(params["mode_repeat"])
            current = str(play_state.get("mode_repeat", "off"))
            play_state["mode_repeat"] = (
                REPEAT_TOGGLE.get(current, "all") if mode == "toggle" else mode
            )
        if "action" in params:
            action = str(params["action"])
            current = str(play_state.get("state", "play"))
            play_state["state"] = (
                PLAY_ACTION_TOGGLE.get(current, "play")
                if action == "toggle"
                else action
            )
        if "position" in params:
            play_state["position"] = params["position"]
        if "skip_track" in params:
            self.skipped_tracks.append(int(params["skip_track"]))
        return {ep.PLAY_STATE}


def create_app(device: FakeStreamMagicDevice) -> web.Application:
    """Build an aiohttp app serving the device on the device's `/smoip` endpoint."""

    async def smoip(request: web.Request) -> web.WebSocketResponse:
        websocket = web.WebSocketResponse()
        await websocket.prepare(request)
        device.connections.append(websocket)
        try:
            async for message in websocket:
                if message.type != WSMsgType.TEXT:
                    continue
                for response in device.handle(json.loads(message.data)):
                    await websocket.send_json(response)
        finally:
            device.connections.remove(websocket)
        return websocket

    app = web.Application()
    app.router.add_get("/smoip", smoip)
    return app


async def wait_until(predicate: Callable[[], bool], timeout: float = 1.0) -> None:
    """Wait for state pushed over the fake websocket to reach the client."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while not predicate():
        if loop.time() >= deadline:
            raise AssertionError("Condition was not met before the timeout")
        await asyncio.sleep(0)
