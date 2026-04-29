[← 12 Open Source Open Hardware Home](../README.md) · [← Open Boards Home](README.md) · [← Project Home](../../../README.md)

# Hobbyist & Development Boards

The boards driving the open-source FPGA renaissance — affordable, open-toolchain-compatible, and community-supported.

---

## Comparison Matrix

| Board | FPGA | LUTs | RAM | Price | Open Toolchain | Special |
|---|---|---|---|---|---|---|
| **ULX3S** | Lattice ECP5 LFE5U-85F | 84K | 32 MB SDRAM | ~$130 | ✅ Yosys + nextpnr + Trellis | ESP32 companion, HDMI, GPIO, PMOD, open HW |
| **OrangeCrab** | Lattice ECP5 LFE5U-25F | 25K | 128 MB DDR3 | ~$100 | ✅ Yosys + nextpnr + Trellis | Feather form-factor, USB-C, battery charger |
| **iCEBreaker** | Lattice iCE40UP5K | 5K | 128 KB SPRAM | ~$70 | ✅ Yosys + nextpnr + IceStorm | PMOD, RGB LED, best for learning |
| **TinyFPGA BX** | Lattice iCE40LP8K | 8K | 128 KB SPRAM | ~$50 | ✅ Yosys + nextpnr + IceStorm | USB bootloader, tiny, breadboard-friendly |
| **ButterStick** | Lattice ECP5 LFE5U-85F | 85K | 256 MB DDR3 | ~$180 | ✅ Yosys + nextpnr + Trellis | FMC connector, GbE, highest open-spec ECP5 |
| **Tang Nano 9K** | Gowin GW1NR-9 | 8.6K | 64 MB PSRAM | ~$15 | 🟡 Gowin EDU (Apicula maturing) | Cheapest, HDMI, USB-C, breadboardable |
| **Tang Nano 20K** | Gowin GW2AR-18 | 20K | 64 MB PSRAM | ~$25 | 🟡 Gowin EDU (Apicula maturing) | More LUTs, still ultra-cheap |
| **Colorlight i5** | Lattice ECP5 LFE5U-25F | 25K | 32 MB SDRAM | ~$15 | ✅ Yosys + nextpnr + Trellis | Repurposed LED controller — see [repurposed_boards.md](repurposed_boards.md) |

## Selection Guide

| I want... | Board |
|---|---|
| The best open-source FPGA board | **ULX3S** — ESP32 + ECP5 + full open HW |
| Portable, battery-powered FPGA | **OrangeCrab** — Feather, USB-C, LiPo charger |
| To learn FPGAs from scratch | **iCEBreaker** or **TinyFPGA BX** |
| Maximum open LUTs per dollar | **Colorlight i5** ($15 for 25K LUTs) |
| Cheapest possible entry | **Tang Nano 9K** ($15, HDMI out) |

---

## Original Stub Description

**ULX3S** (ECP5, open HW, ESP32 companion), **OrangeCrab** (ECP5, Feather form-factor, DDR3), **iCEBreaker** (iCE40, PMOD), **TinyFPGA BX**, **ButterStick** (ECP5), **Tang Nano** series (Gowin, ultra-cheap) — comparison matrix: chip, LUTs, RAM, price, open toolchain support

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
