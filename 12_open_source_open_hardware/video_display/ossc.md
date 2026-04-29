[← 12 Open Source Open Hardware Home](../README.md) · [← Video Display Home](README.md) · [← Project Home](../../../README.md)

# OSSC — Open Source Scan Converter

The OSSC (Open Source Scan Converter) is the gold standard for zero-lag analog-to-digital video conversion — turning retro console RGB signals into pristine HDMI output, all in FPGA hardware.

---

## Hardware

| Version | FPGA | Inputs | Output | Features |
|---|---|---|---|---|
| **OSSC Classic (1.6)** | Lattice ECP3 LFE3-35EA (33K LUT) | SCART, Component (YPbPr), VGA (RGBHV) | HDMI/DVI 1.0 | Line 2×/3×/4×/5×, scanlines, 240p/480i/288p/576i |
| **OSSC Pro** | Intel Cyclone V (49K LE) | SCART, Component, VGA, HDMI IN (pass-through) | HDMI 2.0 | 4K upscaling, framebuffer, adaptive line multiplication, HDR, advanced deinterlacing |

## How It Works

```
Analog RGB/YPbPr (240p – 1080i)
    │
    ▼
TVP7002 ADC (or ADV7441 for OSSC Pro)
    │
    ▼
FPGA — line buffer + line multiplication logic
    │
    ▼
TMDS encoder → HDMI output (480p – 1200p)
```

### Line Multiplication Modes

| Mode | Effect | Best For |
|---|---|---|
| **Passthrough** | Same resolution, zero processing | Bypassing internal TV upscalers |
| **Line 2×** | 240p → 480p | Most monitors, lowest latency |
| **Line 3×** | 240p → 720p | HD displays |
| **Line 4×** | 240p → 960p | 1920×1200 monitors |
| **Line 5×** | 240p → 1200p | High-res CRT replacements, 1600×1200 monitors |

## Key Advantage: Zero Lag

Unlike traditional scalers that buffer entire frames, the OSSC operates on **scanlines** — each line is processed and output immediately. Total latency: **\u003c1 scanline** (\u003c64 μs at 15 kHz), imperceptible to humans.

## Open Source Status

- **Hardware**: Open schematics, gerbers available (OSSC Classic)
- **Firmware**: Open-source VHDL on GitHub (marqs85/ossc)
- **Community**: Active forums, custom firmware forks, 3D-printed case designs

---

## Original Stub Description

**OSSC** — Open Source Scan Converter (Lattice ECP3), zero-lag analog RGB/YPbPr → HDMI, line multiplication (2x/3x/4x/5x), scanlines, OSSC Pro successor (Cyclone V, advanced features)

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](../../README.md)
- [README.md](README.md)
