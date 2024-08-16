"""Asynchronous Python client for StreamMagic API."""

from .exceptions import StreamMagicError, StreamMagicConnectionError
from .models import Info, PlayStateMetadata, PlayState, State, Source
from .stream_magic import StreamMagicClient
__all__ = [
    "StreamMagicClient",
    "StreamMagicError",
    "StreamMagicConnectionError",
    "Info",
    "Source",
    "State",
    "PlayState",
    "PlayStateMetadata"
]