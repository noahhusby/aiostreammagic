# Cambridge Audio StreamMagic EQ API Guide

## API Endpoints

### Base URL Format

``` bash
http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1
```

Replace `<DEVICE_IP>` with your Cambridge Audio device's IP address.

### EQ Control Commands

#### Enable/Disable EQ

```bash
# Turn EQ ON
curl "http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1&user_eq=true"

# Turn EQ OFF  
curl "http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1&user_eq=false"
```

#### Apply EQ Preset

```bash
# Set EQ bands
curl "http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1&user_eq_bands=<EQ_PARAMETERS>"
```

## EQ Parameter Format

``` bash
user_eq_bands=0,,,gain,|1,,,gain,|2,,,gain,|3,,,gain,|4,,,gain,|5,,,gain,|6,,,gain,
```

### URL Encoding Reference

- `,` becomes `%2C`
- `|` becomes `%7C`
- `-` remains `-` (negative values)

## EQ Band Mapping (Estimated Frequencies)

Based on typical 7-band EQ distributions:

- **Band 0**: ~60Hz (Sub-bass)
- **Band 1**: ~170Hz (Bass)  
- **Band 2**: ~310Hz (Low-mid)
- **Band 3**: ~600Hz (Mid)
- **Band 4**: ~1kHz (Upper-mid)
- **Band 5**: ~3kHz (Presence)
- **Band 6**: ~6kHz+ (Treble)

## Complete EQ Preset Analysis

| Preset | 60Hz | 170Hz | 310Hz | 600Hz | 1kHz | 3kHz | 6kHz+ | Characteristics |
|--------|------|-------|-------|-------|------|------|-------|----------------|
| **Normal (Flat)** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Completely flat - no EQ adjustment |
| **Bass Boost** | +3.0 | +3.0 | +1.0 | 0.0 | -1.0 | -0.5 | -0.3 | Strong bass boost with slight treble reduction - warm, full sound |
| **Bass Reduction** | -4.6 | -1.8 | -0.6 | 0.0 | +0.6 | +0.4 | 0.0 | Deep bass reduction with slight upper-mid boost - thinner sound |
| **Voice Clarity** | -6.0 | -3.4 | +3.0 | +3.0 | +3.0 | +2.2 | -1.4 | Aggressive bass cut with strong midrange boost - optimized for speech clarity |
| **Treble Boost** | 0.0 | 0.0 | 0.0 | 0.0 | +0.6 | +1.8 | +3.0 | Clean treble boost - leaves bass untouched, progressively boosts highs |
| **Treble Reduction** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | -1.2 | -4.2 | Reduces upper frequencies - warmer, less bright sound |
| **TV** | -1.9 | -0.8 | +1.0 | +1.0 | +0.8 | 0.0 | -0.8 | Midrange focus with bass/treble reduction - dialog clarity for TV |
| **Movie** | 0.0 | +1.4 | -0.4 | -2.0 | -0.6 | +0.6 | +1.1 | Scooped mids with bass/treble emphasis - classic cinema "smile curve" |
| **Gaming** | +3.0 | +3.0 | +1.0 | -1.0 | -1.0 | +0.6 | -0.2 | Strong bass boost with scooped mids - enhanced impact sounds |

### Raw Parameter Strings

```bash
# Bass Boost
0,,,3.0,|1,,,3.0,|2,,,1.0,|3,,,0.0,|4,,,-1.0,|5,,,-0.5,|6,,,-0.3,

# Bass Reduction
0,,,-4.6,|1,,,-1.8,|2,,,-0.6,|3,,,0.0,|4,,,0.6,|5,,,0.4,|6,,,0.0,

# Voice Clarity
0,,,-6.0,|1,,,-3.4,|2,,,3.0,|3,,,3.0,|4,,,3.0,|5,,,2.2,|6,,,-1.4,

# Treble Boost
0,,,0.0,|1,,,0.0,|2,,,0.0,|3,,,0.0,|4,,,0.6,|5,,,1.8,|6,,,3.0,

# Treble Reduction
0,,,0.0,|1,,,0.0,|2,,,0.0,|3,,,0.0,|4,,,0.0,|5,,,-1.2,|6,,,-4.2,

# TV
0,,,-1.9,|1,,,-0.8,|2,,,1.0,|3,,,1.0,|4,,,0.8,|5,,,0.0,|6,,,-0.8,

# Movie
0,,,0.0,|1,,,1.4,|2,,,-0.4,|3,,,-2.0,|4,,,-0.6,|5,,,0.6,|6,,,1.1,

# Gaming
0,,,3.0,|1,,,3.0,|2,,,1.0,|3,,,-1.0,|4,,,-1.0,|5,,,0.6,|6,,,-0.2,

# Normal/Flat
0,,,0.0,|1,,,0.0,|2,,,0.0,|3,,,0.0,|4,,,0.0,|5,,,0.0,|6,,,0.0,
```

## Complete API Commands for All Presets

### Basic EQ Control

```bash
# Enable EQ
curl "http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1&user_eq=true"

# Disable EQ
curl "http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1&user_eq=false"
```

### Preset Commands (URL Encoded)

#### Presets by Cambridge Audio

```bash
# Bass Boost
curl "http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1&user_eq_bands=0%2C%2C%2C3.0%2C%7C1%2C%2C%2C3.0%2C%7C2%2C%2C%2C1.0%2C%7C3%2C%2C%2C0.0%2C%7C4%2C%2C%2C-1.0%2C%7C5%2C%2C%2C-0.5%2C%7C6%2C%2C%2C-0.3%2C"

# Bass Reduction 
curl "http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1&user_eq_bands=0%2C%2C%2C-4.6%2C%7C1%2C%2C%2C-1.8%2C%7C2%2C%2C%2C-0.6%2C%7C3%2C%2C%2C0.0%2C%7C4%2C%2C%2C0.6%2C%7C5%2C%2C%2C0.4%2C%7C6%2C%2C%2C0.0%2C"

# Voice Clarity
curl "http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1&user_eq_bands=0%2C%2C%2C-6.0%2C%7C1%2C%2C%2C-3.4%2C%7C2%2C%2C%2C3.0%2C%7C3%2C%2C%2C3.0%2C%7C4%2C%2C%2C3.0%2C%7C5%2C%2C%2C2.2%2C%7C6%2C%2C%2C-1.4%2C"

# Treble Boost
curl "http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1&user_eq_bands=0%2C%2C%2C0.0%2C%7C1%2C%2C%2C0.0%2C%7C2%2C%2C%2C0.0%2C%7C3%2C%2C%2C0.0%2C%7C4%2C%2C%2C0.6%2C%7C5%2C%2C%2C1.8%2C%7C6%2C%2C%2C3.0%2C"

# Treble Reduction
curl "http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1&user_eq_bands=0%2C%2C%2C0.0%2C%7C1%2C%2C%2C0.0%2C%7C2%2C%2C%2C0.0%2C%7C3%2C%2C%2C0.0%2C%7C4%2C%2C%2C0.0%2C%7C5%2C%2C%2C-1.2%2C%7C6%2C%2C%2C-4.2%2C"

# TV
curl "http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1&user_eq_bands=0%2C%2C%2C-1.9%2C%7C1%2C%2C%2C-0.8%2C%7C2%2C%2C%2C1.0%2C%7C3%2C%2C%2C1.0%2C%7C4%2C%2C%2C0.8%2C%7C5%2C%2C%2C0.0%2C%7C6%2C%2C%2C-0.8%2C"

# Movie
curl "http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1&user_eq_bands=0%2C%2C%2C0.0%2C%7C1%2C%2C%2C1.4%2C%7C2%2C%2C%2C-0.4%2C%7C3%2C%2C%2C-2.0%2C%7C4%2C%2C%2C-0.6%2C%7C5%2C%2C%2C0.6%2C%7C6%2C%2C%2C1.1%2C"

# Gaming
curl "http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1&user_eq_bands=0%2C%2C%2C3.0%2C%7C1%2C%2C%2C3.0%2C%7C2%2C%2C%2C1.0%2C%7C3%2C%2C%2C-1.0%2C%7C4%2C%2C%2C-1.0%2C%7C5%2C%2C%2C0.6%2C%7C6%2C%2C%2C-0.2%2C"

# Normal/Flat
curl "http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1&user_eq_bands=0%2C%2C%2C0.0%2C%7C1%2C%2C%2C0.0%2C%7C2%2C%2C%2C0.0%2C%7C3%2C%2C%2C0.0%2C%7C4%2C%2C%2C0.0%2C%7C5%2C%2C%2C0.0%2C%7C6%2C%2C%2C0.0%2C"
```

#### Custom Preset Examples

```bash
# Balanced Hi-Fi
curl "http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1&user_eq_bands=0%2C%2C%2C1.0%2C%7C1%2C%2C%2C0.5%2C%7C2%2C%2C%2C0.0%2C%7C3%2C%2C%2C0.0%2C%7C4%2C%2C%2C0.0%2C%7C5%2C%2C%2C0.5%2C%7C6%2C%2C%2C1.0%2C"

# Podcast Optimized
curl "http://<DEVICE_IP>/smoip/zone/audio?zone=ZONE1&user_eq_bands=0%2C%2C%2C-3.0%2C%7C1%2C%2C%2C-1.0%2C%7C2%2C%2C%2C2.0%2C%7C3%2C%2C%2C2.5%2C%7C4%2C%2C%2C2.0%2C%7C5%2C%2C%2C1.0%2C%7C6%2C%2C%2C-2.0%2C"
```

## Preset Categories

### **Bass-Heavy** (Gaming, Bass Boost - very similar)

Both feature strong low-end emphasis but with subtle differences:

- **Bass Boost**: More treble reduction (-0.5dB at 3kHz, -0.3dB at 6kHz+)
- **Gaming**: Less treble reduction (+0.6dB at 3kHz, -0.2dB at 6kHz+)

### **Dialog-Focused** (TV, Voice Clarity)  

Midrange emphasis but different approaches - TV is gentler

### **Balanced** (Normal, Treble Boost, Treble Reduction)

Flat or gentle frequency adjustments

### **Cinema** (Movie)

Classic "smile curve" for immersive sound

### **Tonal Shaping** (Bass Reduction)

Dramatic frequency reshaping for specific needs

## Technical Notes

- **Gain Range**: -6dB to +3dB across all bands
- **Zone Support**: Multi-room capability (ZONE1, ZONE2, etc.)
- **API Availability**: Introduced in recent StreamMagic firmware updates
- **Real-time Updates**: Changes apply immediately without restart
- **Persistence**: Settings persist across power cycles when saved
