"""Models for StreamMagic."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


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
    preferred_order: int = field(metadata=field_options(alias="preferred_order"))


@dataclass
class State(DataClassORJSONMixin):
    """Data class representing StreamMagic state."""

    source: str = field(metadata=field_options(alias="source"))
    power: bool = field(metadata=field_options(alias="power"))
    pre_amp_mode: bool = field(metadata=field_options(alias="pre_amp_mode"))
    pre_amp_state: bool = field(metadata=field_options(alias="pre_amp_state"))
    volume_step: int = field(metadata=field_options(alias="volume_step"), default=None)
    volume_db: int = field(metadata=field_options(alias="volume_db"), default=None)
    volume_percent: int = field(
        metadata=field_options(alias="volume_percent"), default=None
    )
    mute: bool = field(metadata=field_options(alias="mute"), default=False)


@dataclass
class PlayState(DataClassORJSONMixin):
    """Data class representing StreamMagic play state."""

    state: str = field(metadata=field_options(alias="state"), default="not_ready")
    metadata: PlayStateMetadata = field(
        metadata=field_options(alias="metadata"), default=None
    )
    presettable: bool = field(
        metadata=field_options(alias="presettable"), default=False
    )
    position: int = field(metadata=field_options(alias="position"), default=None)
    mode_repeat: str = field(metadata=field_options(alias="mode_repeat"), default="off")
    mode_shuffle: str = field(
        metadata=field_options(alias="mode_shuffle"), default="off"
    )


@dataclass
class PlayStateMetadata(DataClassORJSONMixin):
    """Data class representing StreamMagic play state metadata."""

    class_name: str = field(metadata=field_options(alias="class"), default=None)
    source: str = field(metadata=field_options(alias="source"), default=None)
    name: str = field(metadata=field_options(alias="name"), default=None)
    title: str = field(metadata=field_options(alias="title"), default=None)
    art_url: str = field(metadata=field_options(alias="art_url"), default=None)
    sample_format: str = field(
        metadata=field_options(alias="sample_format"), default=None
    )
    mqa: str = field(metadata=field_options(alias="mqa"), default=None)
    signal: bool = field(metadata=field_options(alias="signal"), default=None)
    codec: str = field(metadata=field_options(alias="codec"), default=None)
    lossless: bool = field(metadata=field_options(alias="lossless"), default=None)
    sample_rate: int = field(metadata=field_options(alias="sample_rate"), default=None)
    bitrate: int = field(metadata=field_options(alias="bitrate"), default=None)
    encoding: str = field(metadata=field_options(alias="encoding"), default=None)
    radio_id: int | None = field(metadata=field_options(alias="radio_id"), default=None)
    duration: int | None = field(metadata=field_options(alias="duration"), default=None)
    artist: str | None = field(metadata=field_options(alias="artist"), default=None)
    station: str | None = field(metadata=field_options(alias="station"), default=None)
    album: str | None = field(metadata=field_options(alias="album"), default=None)


@dataclass
class NowPlaying(DataClassORJSONMixin):
    """Data class representing NowPlaying state."""

    controls: list[TransportControl] = field(
        metadata=field_options(alias="controls"), default=None
    )


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
