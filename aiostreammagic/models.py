"""Models for StreamMagic."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


class TransportControl(StrEnum):
    """Control enum."""

    PAUSE = "pause"
    PLAY = "play"
    PLAY_PAUSE = "play_pause"
    TOGGLE_SHUFFLE = "toggle_shuffle"
    TOGGLE_REPEAT = "toggle_repeat"
    TRACK_NEXT = "track_next"
    TRACK_PREVIOUS = "track_previous"
    SEEK = "seek"
    STOP = "stop"


class ShuffleMode(StrEnum):
    """Shuffle mode."""

    OFF = "off"
    ALL = "all"
    TOGGLE = "toggle"


class RepeatMode(StrEnum):
    """Repeat mode."""

    OFF = "off"
    ALL = "all"
    TOGGLE = "toggle"


class CallbackType(StrEnum):
    """Callback type."""

    STATE = "state"
    CONNECTION = "connection"


class DisplayBrightness(StrEnum):
    """Display brightness."""

    BRIGHT = "bright"
    DIM = "dim"
    OFF = "off"
    NONE = "none"


class ControlBusMode(StrEnum):
    """Control bus mode."""

    AMPLIFIER = "amplifier"
    RECEIVER = "receiver"
    OFF = "off"


@dataclass
class Info(DataClassORJSONMixin):
    """Cambridge Audio device metadata."""

    name: str = field(metadata=field_options(alias="name"))
    model: str = field(metadata=field_options(alias="model"))
    timezone: str = field(metadata=field_options(alias="timezone"))
    locale: str = field(metadata=field_options(alias="locale"))
    udn: str = field(metadata=field_options(alias="udn"))
    unit_id: str = field(metadata=field_options(alias="unit_id"))
    api_version: str = field(metadata=field_options(alias="api"))


@dataclass
class Source(DataClassORJSONMixin):
    """Data class representing StreamMagic source."""

    id: str = field(metadata=field_options(alias="id"))
    name: str = field(metadata=field_options(alias="name"))
    default_name: str = field(metadata=field_options(alias="default_name"))
    nameable: bool = field(metadata=field_options(alias="nameable"))
    ui_selectable: bool = field(metadata=field_options(alias="ui_selectable"))
    description: str = field(metadata=field_options(alias="description"))
    description_locale: str = field(metadata=field_options(alias="description_locale"))
    preferred_order: Optional[int] = field(
        metadata=field_options(alias="preferred_order"), default=None
    )


@dataclass
class State(DataClassORJSONMixin):
    """Data class representing StreamMagic state."""

    source: str = field(metadata=field_options(alias="source"))
    power: bool = field(metadata=field_options(alias="power"))
    pre_amp_mode: bool = field(metadata=field_options(alias="pre_amp_mode"))
    pre_amp_state: bool = field(metadata=field_options(alias="pre_amp_state"))
    volume_step: Optional[int] = field(
        metadata=field_options(alias="volume_step"), default=None
    )
    volume_db: Optional[int] = field(
        metadata=field_options(alias="volume_db"), default=None
    )
    volume_percent: Optional[int] = field(
        metadata=field_options(alias="volume_percent"), default=None
    )
    mute: bool = field(metadata=field_options(alias="mute"), default=False)
    audio_output: Optional[str] = field(
        metadata=field_options(alias="audio_output"), default=None
    )
    control_bus: ControlBusMode = field(
        metadata=field_options(alias="cbus"), default=ControlBusMode.OFF
    )


@dataclass
class PlayStateMetadata(DataClassORJSONMixin):
    """Data class representing StreamMagic play state metadata."""

    class_name: Optional[str] = field(
        metadata=field_options(alias="class"), default=None
    )
    source: Optional[str] = field(metadata=field_options(alias="source"), default=None)
    name: Optional[str] = field(metadata=field_options(alias="name"), default=None)
    title: Optional[str] = field(metadata=field_options(alias="title"), default=None)
    art_url: Optional[str] = field(
        metadata=field_options(alias="art_url"), default=None
    )
    sample_format: Optional[str] = field(
        metadata=field_options(alias="sample_format"), default=None
    )
    mqa: Optional[str] = field(metadata=field_options(alias="mqa"), default=None)
    signal: Optional[bool] = field(metadata=field_options(alias="signal"), default=None)
    codec: Optional[str] = field(metadata=field_options(alias="codec"), default=None)
    lossless: Optional[bool] = field(
        metadata=field_options(alias="lossless"), default=None
    )
    sample_rate: Optional[int] = field(
        metadata=field_options(alias="sample_rate"), default=None
    )
    bitrate: Optional[int] = field(
        metadata=field_options(alias="bitrate"), default=None
    )
    encoding: Optional[str] = field(
        metadata=field_options(alias="encoding"), default=None
    )
    radio_id: Optional[int] = field(
        metadata=field_options(alias="radio_id"), default=None
    )
    duration: Optional[int] = field(
        metadata=field_options(alias="duration"), default=None
    )
    artist: Optional[str] = field(metadata=field_options(alias="artist"), default=None)
    station: Optional[str] = field(
        metadata=field_options(alias="station"), default=None
    )
    album: Optional[str] = field(metadata=field_options(alias="album"), default=None)


@dataclass
class PlayState(DataClassORJSONMixin):
    """Data class representing StreamMagic play state."""

    state: str = field(metadata=field_options(alias="state"), default="not_ready")
    metadata: PlayStateMetadata = field(
        metadata=field_options(alias="metadata"), default_factory=PlayStateMetadata
    )
    presettable: bool = field(
        metadata=field_options(alias="presettable"), default=False
    )
    position: Optional[int] = field(
        metadata=field_options(alias="position"), default=None
    )
    mode_repeat: str = field(metadata=field_options(alias="mode_repeat"), default="off")
    mode_shuffle: str = field(
        metadata=field_options(alias="mode_shuffle"), default="off"
    )


@dataclass
class PresetList(DataClassORJSONMixin):
    """Data class representing StreamMagic preset table."""

    start: int = field(metadata=field_options(alias="start"), default=1)
    end: int = field(metadata=field_options(alias="end"), default=99)
    max_presets: int = field(metadata=field_options(alias="max_presets"), default=99)
    presettable: bool = field(
        metadata=field_options(alias="presettable"), default=False
    )
    presets: list[Preset] = field(
        metadata=field_options(alias="presets"), default_factory=list
    )


@dataclass
class Preset(DataClassORJSONMixin):
    """Data class representing StreamMagic preset."""

    preset_id: int = field(metadata=field_options(alias="id"))
    name: str = field(metadata=field_options(alias="name"))
    type: str = field(metadata=field_options(alias="type"))
    preset_class: str = field(metadata=field_options(alias="class"))
    state: str = field(metadata=field_options(alias="state"))
    is_playing: bool = field(metadata=field_options(alias="is_playing"), default=False)
    art_url: Optional[str] = field(
        metadata=field_options(alias="art_url"), default=None
    )
    airable_radio_id: Optional[int] = field(
        metadata=field_options(alias="airable_radio_id"), default=None
    )


@dataclass
class NowPlaying(DataClassORJSONMixin):
    """Data class representing NowPlaying state."""

    controls: list[TransportControl] = field(
        metadata=field_options(alias="controls"), default_factory=list
    )


@dataclass
class AudioOutput(DataClassORJSONMixin):
    """Data class representing StreamMagic audio output."""

    outputs: list[Output] = field(
        metadata=field_options(alias="outputs"), default_factory=list
    )


@dataclass
class Output(DataClassORJSONMixin):
    """Data class representing StreamMagic output."""

    id: str = field(metadata=field_options(alias="id"))
    name: str = field(metadata=field_options(alias="name"))


@dataclass
class Display(DataClassORJSONMixin):
    brightness: DisplayBrightness = field(metadata=field_options(alias="brightness"))


@dataclass
class Update(DataClassORJSONMixin):
    early_update: bool = field(
        metadata=field_options(alias="early_update"), default=False
    )
    update_available: bool = field(
        metadata=field_options(alias="update_available"), default=False
    )
    updating: bool = field(metadata=field_options(alias="updating"), default=False)
