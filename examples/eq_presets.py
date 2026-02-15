"""Example usage of EQ presets."""

import asyncio

from aiostreammagic import (
    StreamMagicClient,
    UserEQ,
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

    # Set EQ using a preset
    async with StreamMagicClient("192.168.1.100") as client:
        try:
            # Use the from_preset helper (recommended)
            eq_settings = UserEQ.from_preset("bass_boost", enabled=True)
            await client.set_equalizer_params(eq_settings)
            print("\nApplied bass_boost preset")
        except ValueError as e:
            print(f"\nError handling example: {e}")


if __name__ == "__main__":
    asyncio.run(main())
