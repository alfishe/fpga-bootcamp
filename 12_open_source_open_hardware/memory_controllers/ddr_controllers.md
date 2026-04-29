[← 12 Open Source Open Hardware Home](../README.md) · [← Memory Controllers Home](README.md) · [← Project Home](../../../README.md)

# Open DDR Controllers

Open-source DDR1/2/3/4 SDRAM controllers for FPGA — comparison across clock speeds, data widths, FPGA families, and interface protocols.

---

## Controller Comparison

| Controller | DDR Gen | Max Clock | Data Width | Interface | FPGA Verified | Repository |
|---|---|---|---|---|---|---|
| **FPGA-DDR-SDRAM** | DDR1 | 200 MHz | 16-bit | AXI-4 | Artix-7, Cyclone IV | WangXuan95/FPGA-DDR-SDRAM |
| **core_ddr3_controller** | DDR3 | 400 MHz (800 MT/s) | 16/32-bit | Wishbone | ECP5, Artix-7 | ultraembedded/core_ddr3_controller |
| **DDR4_controller** | DDR4 | 800 MHz (1600 MT/s) | 32/64-bit | Native FIFO | Kintex-7, Artix-7 | oprecomp/DDR4_controller |
| **LiteDRAM** | DDR1/2/3 | Up to 800 MT/s | 8–64-bit | LiteX native | iCE40, ECP5, Artix-7, Cyclone V | enjoy-digital/litedram |

## Selection Guide

| Scenario | Recommendation | Why |
|---|---|---|
| I need DDR on a cheap board (iCE40/ECP5) | **LiteDRAM** | Only option with full open-toolchain support |
| I want minimal AXI DDR1 for retro/embedded | **FPGA-DDR-SDRAM** | Clean AXI-4 interface, well-tested on Artix-7 |
| I need DDR3 with Wishbone | **core_ddr3_controller** | Mature, Wishbone, verified on multiple platforms |
| I need DDR4 on Xilinx 7-series | **DDR4_controller** | Only open DDR4 option (but needs fast FPGA) |
| I'm using LiteX ecosystem | **LiteDRAM** | Tight LiteX integration, automatic PHY calibration |

## Important Caveats

- **PHY calibration** is the hard part — open controllers often lack the per-bit deskew and read-leveling that vendor IP provides
- **Pin constraints** are board-specific — expect to spend time on pinout validation
- **Vendor DDR IP** (Xilinx MIG, Intel EMIF) is almost always more reliable, but it's proprietary and sometimes tool-locked

---

## Original Stub Description

Open DDR1/2/3/4 controllers: WangXuan95/FPGA-DDR-SDRAM (AXI DDR1), ultraembedded/core_ddr3_controller, oprecomp/DDR4_controller — comparison: max clock, data width, FPGA families tested, interface protocol

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
