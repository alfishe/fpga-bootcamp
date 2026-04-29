[← 12 Open Source Open Hardware Home](../README.md) · [← Memory Controllers Home](README.md) · [← Project Home](../../../README.md)

# Open SDRAM Controllers

Single Data Rate SDRAM controllers — simpler than DDR, easier to implement on low-end FPGAs, widely used in retro computing projects.

---

## Controller Comparison

| Controller | Max Clock | Data Width | Interface | FPGA Verified | Repository |
|---|---|---|---|---|---|
| **sdram-controller** | 166 MHz | 8/16/32-bit | Native (Wishbone adapter available) | iCE40, ECP5, Artix-7 | stffrdhrn/sdram-controller |
| **MiSTer SDRAM** | 133 MHz | 16-bit | Native (parallel) | Cyclone V, Cyclone III | MiSTer-devel/SDRAM_Controller |
| **LiteDRAM** | Up to 166 MHz | 8–32-bit | LiteX native | iCE40, ECP5, Artix-7 | enjoy-digital/litedram |

## When to Use SDRAM Instead of DDR

| SDRAM Advantage | DDR Disadvantage |
|---|---|
| Single-ended clock (no differential pair routing) | Needs differential DQS pairs |
| Simpler state machine (no DQS gating, no ODT) | Complex PHY calibration required |
| Works on 2-layer PCBs | Typically needs 4+ layers for impedance |
| Lower FPGA speed grade requirements | Needs fast IO cells for DDR capture |

## Common Use Cases

- **Retro computing**: Amiga, Atari ST, and console cores use SDRAM because original hardware used similar timing
- **Low-cost FPGA boards**: ULX3S, Tang Nano, TinyFPGA BX — DDR PHY overkill for these
- **Audio/video buffers**: Frame buffers and sample FIFOs where bandwidth is modest (\u003c500 MB/s)

---

## Original Stub Description

Open SDRAM controllers: stffrdhrn/sdram-controller, MiSTer SDRAM controller, **LiteDRAM** (cross-platform, part of LiteX) — comparison: supported FPGAs, max frequency, bus width, burst support

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
