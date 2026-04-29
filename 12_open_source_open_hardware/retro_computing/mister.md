[← 12 Open Source Open Hardware Home](../README.md) · [← Retro Computing Home](README.md) · [← Project Home](../../../README.md)

# MiSTer FPGA — The Open-Source Retro Gaming Platform

MiSTer is the dominant open-source FPGA retro-gaming platform. It uses a DE10-Nano board (Cyclone V SoC) with optional add-on boards (SDRAM, USB hub, I/O board, ADC for analog video) to accurately replicate classic computers and consoles at the hardware level.

---

## Hardware

| Component | Board | Function |
|---|---|---|
| **Main FPGA** | DE10-Nano (Cyclone V 5CSEBA6) | 110K LE, ~80% usable for cores |
| **SDRAM** | 32/64/128 MB SDRAM add-on | Required for most cores (Neo Geo needs 128 MB) |
| **USB Hub** | USB hub v2.1 | Connect keyboard, gamepad, mouse |
| **I/O Board** | Digital I/O or Analog I/O | VGA output, audio, SNAC (native controller), fan |
| **ADC Board** | Analog video input | For digitizing composite/S-Video (tape input for C64, etc.) |

---

## Architecture

```
DE10-Nano
┌──────────────────────────────┐
│ HPS (ARM Cortex-A9)          │
│ ├─ Linux (MiSTer main binary)│
│ ├─ HDMI framebuffer          │
│ └─ SD card + USB + Network   │
│                              │
│ FPGA Fabric                  │
│ ├─ Core (e.g., SNES, Genesis)│
│ ├─ SDRAM controller          │
│ └─ scaler (HDMI out)         │
└──────────────────────────────┘
```

The HPS runs Linux for UI/menu/file management. The FPGA runs the actual console/computer core. SDRAM on GPIO header provides memory for game ROMs.

---

## Key Cores

| Console/Computer | Core Name | Accuracy | Notes |
|---|---|---|---|
| NES | NES | Cycle-accurate | Supports FDS, mapper chips |
| SNES | SNES | Cycle-accurate | SA-1, Super FX, DSP support |
| Sega Genesis/MD | Genesis | Cycle-accurate | Sega CD support via data track |
| Neo Geo | NeoGeo | Near-perfect | Needs 128 MB SDRAM |
| PC Engine / TG16 | TurboGrafx16 | Cycle-accurate | CD-ROM² support |
| Game Boy / GBA | Gameboy | Cycle-accurate | GB, GBC, GBA — all in one core |
| Amiga | Minimig | Very good | AGA, RTG, turbo modes |
| C64 | C64 | Very good | SID emulation, REU support |
| Arcade | Various | Varies | 500+ arcade cores |

---

## Open-Source Status

- **Framework:** GPL v3
- **Cores:** Various licenses (mostly GPL v3, some MIT/BSD)
- **All HDL source on GitHub** — no binary blobs for cores

---

## References

- [MiSTer FPGA Wiki](https://github.com/MiSTer-devel/Wiki_MiSTer/wiki)
- [MiSTer-devel GitHub](https://github.com/MiSTer-devel)
- [DE10-Nano Overview](../open_boards/hobbyist_boards.md)
