"""Example usage of EQ presets."""

import asyncio

from aiostreammagic import (
    StreamMagicClient,
    UserEQ,
    EQ_PRESETS,
    EQ_GAIN_MIN,
    EQ_GAIN_MAX,
    EQ_NUM_BANDS,
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
            # Method 1: Use from_preset (easiest)
            eq_settings = UserEQ.from_preset("bass_boost", enabled=True)
            await client.set_equalizer_params(eq_settings)
            print("\nApplied bass_boost preset")

            # Method 2: Use from_gains for custom EQ
            custom_gains = [1.0, 0.5, 0.0, 0.0, 0.0, 0.5, 1.0]
            custom_eq = UserEQ.from_gains(custom_gains)
            await client.set_equalizer_params(custom_eq)
            print("Applied custom EQ gains")

        except ValueError as e:
            print(f"\nError: {e}")

    # Show EQ constraints
    print("\nEQ constraints:")
    print(f"  - Number of bands: {EQ_NUM_BANDS}")
    print(f"  - Gain range: {EQ_GAIN_MIN} to {EQ_GAIN_MAX} dB")


if __name__ == "__main__":
    asyncio.run(main())
