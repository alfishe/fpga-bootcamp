[← Section Home](../README.md) · [← Project Home](../../README.md)

# 01-C — Lattice Semiconductor

The champion of open-source FPGA toolchains. Lattice's iCE40 and ECP5 families have fully open-source synthesis and placement flows (Yosys + nextpnr), making them the de facto choice for community-driven hardware projects.

## Family Directories

| Directory | Coverage |
|---|---|
| [ice40/](ice40/README.md) | **iCE40** — ultra-low-power open-source pioneer (Project Icestorm). UP5K sweet spot: 5,280 LUTs, 8 DSP, MIPI D-PHY, $8–12 boards (Upduino, iCEBreaker) |
| [ecp5/](ecp5/README.md) | **ECP5** — open-source mid-range powerhouse (Project Trellis). Up to 85K LUTs, 5G SERDES, DDR3, ULX3S, Colorlight, OrangeCrab boards. ECP5 vs Cyclone V vs Artix-7 comparison |
| [crosslink_nx/](crosslink_nx/README.md) | **CrossLink-NX** — 28nm FD-SOI with hard MIPI CSI/DSI. 17K–40K LUTs, LPDDR4, 3× lower soft error rate, 2× lower static power vs ECP5 |
| [certuspro_nx/](certuspro_nx/README.md) | **CertusPro-NX** — scaled FD-SOI: 96K LUTs, PCIe Gen3 ×4, 10.3 Gbps SERDES, large RAM blocks |

## Quick Reference

| Family | Key Devices | Notes |
|---|---|---|
| iCE40 | iCE40HX, iCE40LP, iCE40 UltraPlus | Ultra-low power, open-source Yosys+nextpnr support, iCEBreaker, TinyFPGA |
| **ECP5** | LFE5U, LFE5UM5G (5G SerDes) | Open-source supported powerhouse: ULX3S, OrangeCrab, Colorlight, ButterStick |
| MachXO2/ZO3 | LCMXO2, LCMXO3 | Non-volatile, instant-on, limited open-source people |
| CrossLink-NX / CrossLinkU-NX | LIFCL, LIFCL-U | 28nm FD-SOI, MIPI D-PHY, low power, newer |
| CertusPro-NX | LFCPNX | Higher-end 28nm FD-SOI, SerDes, larger LUT count |
| Avant | LAV | Mid-range 16nm platform, PCIe, 25G SerDes |
