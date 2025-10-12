# Cambridge Audio StreamMagic Audio API Guide

## Features

- Volume limit for streaming services
- Balance control
- Parametric equalizer
- Room compensation (tilt equalizer)
- Audio pipeline (undocumented)

### Technical Notes

- **User EQ Gain Range**: -6dB to +3dB across all bands
- **Tilt EQ Range**: -15 to +15 (room compensation)
- **Balance Range**: -15 (full left) to +15 (full right)
- **Zone Support**: Multi-room capability (ZONE1, ZONE2, etc.)
- **API Availability**: Introduced in recent StreamMagic firmware updates
- **Real-time Updates**: Changes apply immediately without restart
- **Persistence**: Settings persist across power cycles when saved
- **Processing Order**: Tilt EQ → User EQ → Balance → Volume Limiting

### Combined EQ Strategy

1. **Start with Tilt EQ**: Address broad room characteristics
1. **Add User EQ**: Fine-tune specific frequency issues
1. **Adjust Balance**: Compensate for asymmetric room placement
1. **Test and Iterate**: Listen to familiar content and adjust

## Base URL Format

```text
http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1
```

Replace `<DEVICE_IP>` with your Cambridge Audio device's IP address.

The zone parameter is optional and presumably, especially for devices that support only one zone. I will be omitted for most commands in this document.

### Query Current Settings

```bash
# Get current audio settings (JSON response)
curl "http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1"
```

#### JSON Response Format

```json
{
  "zone": "ZONE1",
  "data": {
    "volume_limit_percent": 100,
    "tilt_eq": {
      "enabled": false,
      "intensity": 0
    },
    "user_eq": {
      "enabled": false,
      "bands": [
        {
          "index": 0,
          "filter": "LOWSHELF",
          "freq": 80,
          "gain": 0,
          "q": 0.8
        },
        // ... additional bands
      ]
    },
    "balance": 0,
    "pipeline": "DSP"
  }
}
```

## Volume Limitation

> ⚠️ **Attention:**
>
> The API endpoint for the volume limit seems to have changed with the latest update.
> It used to be `/zone/state`.

From the Cambridge Audio documentation: This sets the maximum volume that other streaming services like AirPlay, Spotify, TIDAL Connect and Google Cast can set. The front panel, remote control and StreamMagic app volume controls can override this setting.

```bash
# Set volume limit (0-100%)
curl "http://<DEVICE_IP>/smoip/zone/audio?volume_limit_percent=<value>"
```

## Balance Control

```bash
# Set stereo balance (range: -15 to +15, 0=center)
curl "http://<DEVICE_IP>/smoip/zone/audio?balance=<value>"
```

Value range is -15 to 15.

### Examples

```bash
# Slight right channel emphasis
curl "http://<DEVICE_IP>/smoip/zone/audio?balance=3"

# Strong left channel emphasis  
curl "http://<DEVICE_IP>/smoip/zone/audio?balance=-8"
```

## Parametric Equalizer

### Enable/Disable EQ

```bash
# Enable EQ
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq=true"

# Disable EQ
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq=false"
```

### Apply EQ Settings

The Cambridge Audio StreamMagic API allows modification of individual EQ band parameters. You can customize frequency, Q factor, and potentially filter types for each band.

```bash
# Set EQ bands
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq_bands=<EQ_PARAMETERS>"
```

The parameters for each band need to be provided in the format

```text
user_eq_bands=[index],[filter],[freq],[gain],[q]
```

To change multiple bands at once separate the parameters for each band with a `|`:

```text
user_eq_bands=[index],[filter],[freq],[gain],[q]|1,[filter],[freq],[gain],[q]|2,[filter],[freq],[gain],[q]|3,[filter],[freq],[gain],[q]|4,[filter],[freq],[gain],[q]|5,[filter],[freq],[gain],[q]|6,[filter],[freq],[gain],[q]
```

> ℹ️ Special characters should be encoded for URLs:
>
> - `,` becomes `%2C`
> - `|` becomes `%7C`

#### Parameters

- `index`: Band number (0-6)
- `filter`: Filter type (LOWSHELF, PEAKING, HIGHSHELF, LOWPASS, HIGHPASS, NOTCH)
- `freq`: Frequency in Hz (20 Hz to 20 kHz)
- `gain`: Gain in dB (-6 dB to 3 dB)
- `q`: Q factor (API seems to accept any value (0-100 confirmed), but a range from 0.1 to 10 seems reasonable)

**Note**: Filter type modification requires further testing to confirm supported values.

#### Parameter Modification Rules

1. **Empty Parameters**: Leave any field empty to preserve current values
2. **Comma Placement**: Always include commas as separators, even for empty parameters
3. **Selective Updates**: You can update only specific bands while leaving others unchanged
4. **Mixed Modifications**: Combine frequency, gain, and Q changes in a single request

### Default Values

- **Band 0**: 80Hz (LOWSHELF, Q=0.8) - Sub-bass
- **Band 1**: 120Hz (PEAKING, Q=1.24) - Bass  
- **Band 2**: 315Hz (PEAKING, Q=1.24) - Low-mid
- **Band 3**: 800Hz (PEAKING, Q=1.24) - Mid
- **Band 4**: 2000Hz (PEAKING, Q=1.24) - Upper-mid
- **Band 5**: 5000Hz (PEAKING, Q=1.24) - Presence
- **Band 6**: 8000Hz (HIGHSHELF, Q=0.8) - Treble

### Custom Parameter Examples

#### Change Only Band 0 Frequency

```bash
# Change Band 0 to 100Hz, preserve all other settings
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq_bands=0,,100,,"
```

#### Change Only Band 2 Q Factor

```bash
# Change Band 2 Q to 2.0, preserve all other settings
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq_bands=2,,,,2.0"
```

#### Change Multiple Parameters for One Band

```bash
# Change Band 3: frequency to 1000Hz, gain to +2dB, Q to 1.5
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq_bands=3,,1000,2.0,1.5"
```

#### Custom EQ with Modified Frequencies

```bash
# Create custom EQ with shifted crossover points
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq_bands=0,,60,1.0,|1,,100,2.0,|2,,250,0.0,|3,,1000,-1.0,|4,,3000,0.5,|5,,6000,1.0,|6,,10000,0.5,"
```

### Presets

#### StreamMagic Presets

The presets available in the StreamMagic app will only change the gains for each band. Here are the settings for each preset:

| Preset | 80Hz | 120Hz | 315Hz | 800Hz | 2kHz | 5kHz | 8kHz | Characteristics |
|--------|------|-------|-------|-------|------|------|-------|----------------|
| **Normal (Flat)** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Completely flat - no EQ adjustment |
| **Bass Boost** | +3.0 | +3.0 | +1.0 | 0.0 | -1.0 | -0.5 | -0.3 | Strong bass boost with slight treble reduction - warm, full sound |
| **Bass Reduction** | -4.6 | -1.8 | -0.6 | 0.0 | +0.6 | +0.4 | 0.0 | Deep bass reduction with slight upper-mid boost - thinner sound |
| **Voice Clarity** | -6.0 | -3.4 | +3.0 | +3.0 | +3.0 | +2.2 | -1.4 | Aggressive bass cut with strong midrange boost - optimized for speech clarity |
| **Treble Boost** | 0.0 | 0.0 | 0.0 | 0.0 | +0.6 | +1.8 | +3.0 | Clean treble boost - leaves bass untouched, progressively boosts highs |
| **Treble Reduction** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | -1.2 | -4.2 | Reduces upper frequencies - warmer, less bright sound |
| **TV** | -1.9 | -0.8 | +1.0 | +1.0 | +0.8 | 0.0 | -0.8 | Midrange focus with bass/treble reduction - dialog clarity for TV - gentler than voice clarity |
| **Movie** | 0.0 | +1.4 | -0.4 | -2.0 | -0.6 | +0.6 | +1.1 | Scooped mids with bass/treble emphasis - classic cinema "smile curve" for immersive sound |
| **Gaming** | +3.0 | +3.0 | +1.0 | -1.0 | -1.0 | +0.6 | -0.2 | Strong bass boost with scooped mids - enhanced impact sounds - very similar to bass boost |

##### API Commands for All Presets

```bash
# Normal/Flat
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq_bands=0%2C%2C%2C0.0%2C%7C1%2C%2C%2C0.0%2C%7C2%2C%2C%2C0.0%2C%7C3%2C%2C%2C0.0%2C%7C4%2C%2C%2C0.0%2C%7C5%2C%2C%2C0.0%2C%7C6%2C%2C%2C0.0%2C"

# Bass Boost
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq_bands=0%2C%2C%2C3.0%2C%7C1%2C%2C%2C3.0%2C%7C2%2C%2C%2C1.0%2C%7C3%2C%2C%2C0.0%2C%7C4%2C%2C%2C-1.0%2C%7C5%2C%2C%2C-0.5%2C%7C6%2C%2C%2C-0.3%2C"

# Bass Reduction 
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq_bands=0%2C%2C%2C-4.6%2C%7C1%2C%2C%2C-1.8%2C%7C2%2C%2C%2C-0.6%2C%7C3%2C%2C%2C0.0%2C%7C4%2C%2C%2C0.6%2C%7C5%2C%2C%2C0.4%2C%7C6%2C%2C%2C0.0%2C"

# Voice Clarity
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq_bands=0%2C%2C%2C-6.0%2C%7C1%2C%2C%2C-3.4%2C%7C2%2C%2C%2C3.0%2C%7C3%2C%2C%2C3.0%2C%7C4%2C%2C%2C3.0%2C%7C5%2C%2C%2C2.2%2C%7C6%2C%2C%2C-1.4%2C"

# Treble Boost
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq_bands=0%2C%2C%2C0.0%2C%7C1%2C%2C%2C0.0%2C%7C2%2C%2C%2C0.0%2C%7C3%2C%2C%2C0.0%2C%7C4%2C%2C%2C0.6%2C%7C5%2C%2C%2C1.8%2C%7C6%2C%2C%2C3.0%2C"

# Treble Reduction
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq_bands=0%2C%2C%2C0.0%2C%7C1%2C%2C%2C0.0%2C%7C2%2C%2C%2C0.0%2C%7C3%2C%2C%2C0.0%2C%7C4%2C%2C%2C0.0%2C%7C5%2C%2C%2C-1.2%2C%7C6%2C%2C%2C-4.2%2C"

# TV
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq_bands=0%2C%2C%2C-1.9%2C%7C1%2C%2C%2C-0.8%2C%7C2%2C%2C%2C1.0%2C%7C3%2C%2C%2C1.0%2C%7C4%2C%2C%2C0.8%2C%7C5%2C%2C%2C0.0%2C%7C6%2C%2C%2C-0.8%2C"

# Movie
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq_bands=0%2C%2C%2C0.0%2C%7C1%2C%2C%2C1.4%2C%7C2%2C%2C%2C-0.4%2C%7C3%2C%2C%2C-2.0%2C%7C4%2C%2C%2C-0.6%2C%7C5%2C%2C%2C0.6%2C%7C6%2C%2C%2C1.1%2C"

# Gaming
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq_bands=0%2C%2C%2C3.0%2C%7C1%2C%2C%2C3.0%2C%7C2%2C%2C%2C1.0%2C%7C3%2C%2C%2C-1.0%2C%7C4%2C%2C%2C-1.0%2C%7C5%2C%2C%2C0.6%2C%7C6%2C%2C%2C-0.2%2C"
```

#### Custom Preset Examples

##### Balanced Hi-Fi

```bash
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq_bands=0%2C%2C%2C1.0%2C%7C1%2C%2C%2C0.5%2C%7C2%2C%2C%2C0.0%2C%7C3%2C%2C%2C0.0%2C%7C4%2C%2C%2C0.0%2C%7C5%2C%2C%2C0.5%2C%7C6%2C%2C%2C1.0%2C"
```

##### Podcast Optimized

```bash
curl "http://<DEVICE_IP>/smoip/zone/audio?user_eq_bands=0%2C%2C%2C-3.0%2C%7C1%2C%2C%2C-1.0%2C%7C2%2C%2C%2C2.0%2C%7C3%2C%2C%2C2.5%2C%7C4%2C%2C%2C2.0%2C%7C5%2C%2C%2C1.0%2C%7C6%2C%2C%2C-2.0%2C"
```

## Room Compensation (Tilt EQ)

- **Range**: -15 (bass emphasis) to +15 (treble emphasis)
- **Negative values**: Compensate for overly bright/reflective rooms
- **Positive values**: Compensate for overly dead/absorptive rooms
- **Works independently**: Can be used alongside user EQ bands

```bash
# Enable tilt EQ
curl "http://<DEVICE_IP>/smoip/zone/audio?tilt_eq=true"
# Set intensity (range: -15 to +15)
curl "http://<DEVICE_IP>/smoip/zone/audio?tilt_intensity=<value>"
# Disable tilt EQ
curl "http://<DEVICE_IP>/smoip/zone/audio?tilt_eq=false"
```

### Tilt EQ Settings by Room Type

| Room Characteristic | Tilt Setting | Description |
|-------------------|--------------|-------------|
| **Hard surfaces** (tile, glass, concrete) | -8 to -15 | Reduce brightness, add warmth |
| **Mixed surfaces** (typical living room) | -3 to -8 | Slight warmth adjustment |
| **Neutral room** | 0 | No compensation needed |
| **Soft furnishings** (heavy curtains, carpet) | +3 to +8 | Add clarity and presence |
| **Very dead room** (recording studio) | +8 to +15 | Maximum clarity boost |

```bash
# Examples:
# Warm room compensation (boost bass, reduce treble)
curl "http://<DEVICE_IP>/smoip/zone/audio?tilt_eq=true&tilt_intensity=-10"

# Bright room compensation (reduce bass, boost treble)
curl "http://<DEVICE_IP>/smoip/zone/audio?tilt_eq=true&tilt_intensity=+8"
```

## Audio Pipeline (undocumented)

Functionality tbd. Possible options:

- DSP
- DIRECT

```bash
# Set audio processing pipeline
curl "http://<DEVICE_IP>/smoip/zone/audio?pipeline=DSP"
```
