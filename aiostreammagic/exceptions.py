"""Asynchronous Python client for StreamMagic API."""


class StreamMagicError(Exception):
    """Base class for exceptions in this module."""


class StreamMagicConnectionError(StreamMagicError):
    """StreamMagic connection exception."""
