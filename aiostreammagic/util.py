"""Utility functions for StreamMagic."""

from typing import Optional

from aiostreammagic.models import EQBand


def eq_bands_to_param_string(bands: list[EQBand]) -> str:
    """Format EQ bands as required by the API.

    Args:
        bands: List of EQ bands to format

    Returns:
        Pipe-separated string of band parameters in format:
        "index,filter,freq,gain,q|index,filter,freq,gain,q|..."
    """

    def fmt(val: object, float_fmt: Optional[str] = None) -> str:
        if val is None:
            return ""
        if float_fmt and isinstance(val, float):
            return float_fmt.format(val)
        return str(val)

    return "|".join(
        f"{fmt(band.index)},{fmt(band.filter)},{fmt(band.freq)},{fmt(band.gain, '{:.1f}')},{fmt(band.q, '{:.2f}')}"
        for band in bands
    )
