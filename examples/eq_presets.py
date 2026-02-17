"""Example usage of EQ presets."""

import asyncio

from aiostreammagic import (
    StreamMagicClient,
    EQBand,
    EQ_PRESETS,
)


async def main() -> None:
    """Example of using EQ presets."""
    # List all available presets (useful for UI/select entities)
    print("Available EQ presets:")
    for preset_name in EQ_PRESETS.keys():
        print(f"  - {preset_name}")

    # Get preset gain values (useful for UI sliders)
    bass_boost_gains = EQ_PRESETS["bass_boost"]
    print(f"\nBass boost gains: {bass_boost_gains}")

    # Set EQ using presets and custom values
    async with StreamMagicClient("192.168.x.x") as client:
        try:
            # Method 1: Use set_equalizer_preset (easiest)
            await client.set_equalizer_preset("bass_boost")
            print("\nApplied bass_boost preset")

            # Method 2: Build custom EQ from gains
            custom_gains = [1.0, 0.5, 0.0, 0.0, 0.0, 0.5, 1.0]
            bands = [EQBand(index=i, gain=gain) for i, gain in enumerate(custom_gains)]
            await client.set_equalizer_params(bands)
            print("Applied custom EQ gains")

        except ValueError as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
