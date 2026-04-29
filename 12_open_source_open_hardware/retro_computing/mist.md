[← 12 Open Source Open Hardware Home](../README.md) · [← Retro Computing Home](README.md) · [← Project Home](../../../README.md)

# MiST — The Original Open Retro Platform

MiST (AMIGA + ST = MiST) is the original open-source FPGA retro-hardware platform — launched in 2013, it pioneered the concept of cycle-accurate hardware recreation on affordable FPGA boards.

---

## Hardware

| Component | Spec |
|---|---|
| **FPGA** | Intel Cyclone III EP3C25 (25K LE) |
| **RAM** | 32 MB SDRAM |
| **Storage** | SD card slot |
| **Video** | VGA output (24-bit) |
| **Audio** | 3.5 mm stereo jack (sigma-delta DAC) |
| **Input** | 2× DB9 joystick ports, PS/2 keyboard/mouse |
| **Connectivity** | USB (for MIDI, serial, HID), MIDI IN/OUT |
| **MCU** | ARM STM32 (system controller, firmware update) |

## Architecture

The STM32 ARM MCU is the **system controller**, not a co-processor — it handles:
- SD card FAT filesystem (loading ROMs/floppy images)
- Firmware update (FPGA bitstream + MCU firmware from SD)
- OSD menu (on-screen display overlay controlled by the MCU)
- Input routing (USB HID → FPGA core)

This architecture (MCU host + FPGA fabric) became the template for later platforms:

```
MiST (2013)
  ├─► MiSTer (2017) — Cyclone V, ARM HPS replaces MCU
  ├─► SiDi / SiDi128 — Cyclone IV / Cyclone V, similar MCU architecture
  └─► MiSTeX — Multiple FPGA targets, OSSC-like sampling
```

## Legacy and Current Status

| Aspect | Assessment |
|---|---|
| **Still relevant?** | Yes — many cores run on MiST first, then get ported to MiSTer |
| **Hardware availability** | Clones available (SiDi, QMTech Cyclone III boards) |
| **Core count** | 50+ cores (Amiga, ST, C64, consoles, arcade) |
| **Limitation** | Cyclone III is 10-generation old — misses modern I/O standards |

---

## Original Stub Description

**MiST** — original open retro-hardware platform (Cyclone III), predecessor and simpler sibling to MiSTer

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
