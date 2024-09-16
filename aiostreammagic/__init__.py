"""
.. include:: ../README.md
"""

from .exceptions import StreamMagicError, StreamMagicConnectionError
from .models import (
    Info,
    PlayStateMetadata,
    PlayState,
    State,
    Source,
    NowPlaying,
    TransportControl,
    RepeatMode,
    ShuffleMode,
)
from .stream_magic import StreamMagicClient

__all__ = [
    "StreamMagicClient",
    "StreamMagicError",
    "StreamMagicConnectionError",
    "Info",
    "Source",
    "State",
    "PlayState",
    "PlayStateMetadata",
    "NowPlaying",
    "TransportControl",
    "ShuffleMode",
    "RepeatMode",
]
