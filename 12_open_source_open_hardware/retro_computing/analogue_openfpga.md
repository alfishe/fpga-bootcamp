[← 12 Open Source Open Hardware Home](../README.md) · [← Retro Computing Home](README.md) · [← Project Home](../../../README.md)

# Analogue Pocket + openFPGA

The Analogue Pocket is a commercial handheld gaming device built on a Cyclone V FPGA. Its **openFPGA** platform lets 3rd-party developers create FPGA cores for it — a unique bridge between commercial hardware and the open FPGA community.

---

## Hardware

| Component | Spec |
|---|---|
| **Main FPGA** | Intel Cyclone V (49K LE) |
| **Secondary FPGA** | Intel Cyclone 10 (16K LE) — system management |
| **Display** | 1600×1440 LCD (615 ppi) — 10× Game Boy resolution |
| **RAM** | 64 MB SDRAM (shared between FPGA's frame buffer and core memory) |
| **Cartridge Slot** | Physical cartridge adapter for GB/GBC/GBA |
| **Controls** | D-pad, ABXY, L/R shoulder, Start/Select |

## openFPGA Platform

Analogue's **openFPGA** is a development framework that allows 3rd-party FPGA cores to run on the Pocket:

| Feature | Details |
|---|---|
| **Core format** | JSON metadata + bitstream |
| **Access to** | Display, controls, SDRAM, cartridge slot, SD card |
| **Development** | Standard Quartus flow, Analogue SDK |
| **Distribution** | Community repositories, no Analogue approval needed |
| **Not Open Source Hardware** | The Pocket's own hardware design is proprietary — openFPGA is an API, not open HW |

## Available Cores (Community)

- **Console cores**: NES, SNES, Genesis, PC Engine, Neo Geo, Atari 2600/7800, Game Gear, Lynx
- **Arcade cores**: Many via MiSTer core ports (Pocket has less fabric but similar architecture)
- **Computer cores**: Amiga 500 (Minimig-like), C64

## Relationship with MiSTer

| Aspect | MiSTer | Analogue Pocket |
|---|---|---|
| **FPGA** | Cyclone V (110K LE on DE10-Nano) | Cyclone V (49K LE) |
| **Openness** | Fully open (hardware + software + cores) | Partially open (openFPGA API, closed hardware) |
| **Portability** | No (needs monitor + DE10-Nano + USB hub) | Yes (handheld, self-contained) |
| **Core availability** | 100+ cores | 50+ cores (subset of MiSTer, ported) |
| **Cost** | ~$250+ (fully set up) | $220 |

---

## Original Stub Description

**Analogue Pocket + openFPGA** — commercial handheld with open 3rd-party core development platform, Cyclone V

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
