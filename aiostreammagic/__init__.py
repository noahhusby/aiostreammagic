"""
.. include:: ../README.md
"""

from .exceptions import StreamMagicConnectionError, StreamMagicError
from .models import (
    EQ_PRESETS,
    Audio,
    ControlBusMode,
    EQBand,
    EQFilterType,
    Info,
    NowPlaying,
    PlayState,
    PlayStateMetadata,
    RepeatMode,
    ShuffleMode,
    Source,
    State,
    TransportControl,
    UserEQ,
)
from .stream_magic import StreamMagicClient

__all__ = [
    "EQ_PRESETS",
    "Audio",
    "ControlBusMode",
    "EQBand",
    "EQFilterType",
    "Info",
    "NowPlaying",
    "PlayState",
    "PlayStateMetadata",
    "RepeatMode",
    "ShuffleMode",
    "Source",
    "State",
    "StreamMagicClient",
    "StreamMagicConnectionError",
    "StreamMagicError",
    "TransportControl",
    "UserEQ",
]
