[← Section Home](../README.md) · [← Project Home](../../README.md)

# 01-B — Xilinx / AMD

The market leader in FPGA density and tooling maturity. Covers the 7-series (the workhorse generation), UltraScale+ (high-performance), Versal (ACAP with AI engines), and the Zynq embedded SoC families.

## Family Directories

| Directory | Coverage |
|---|---|
| [7series/](7series/README.md) | **7-Series (28nm)** — Spartan-7, Artix-7, Kintex-7, Virtex-7, Zynq-7000 (SoC with dual Cortex-A9, ACP cache coherency). Zynq vs Cyclone V SoC comparison included |
| [ultrascale_plus/](ultrascale_plus/README.md) | **UltraScale & UltraScale+ (20/16nm)** — Kintex/Virtex UltraScale+, Zynq MPSoC (quad A53 + dual R5F, GPU, VCU), RFSoC (direct RF ADCs/DACs). URAM, CARRY8, dense CLBs |
| [versal/](versal/README.md) | **Versal ACAP (7nm)** — AI Engines (400-tile VLIW SIMD arrays, ~4 TFLOPS), NoC (2D mesh), PCIe Gen5, 112G PAM4. Xilinx vs Intel generation comparison table |

## Quick Reference

| Family | Key Devices | Notes |
|---|---|---|
| **7-series** | Artix-7 (XA7), Kintex-7 (XK7), Virtex-7 (XV7), Zynq-7000 (XZ7) | 28nm. Workhorse generation, Vivado supported, wide open-source toolchain progress |
| UltraScale | Kintex/Virtex UltraScale (XKU/XVU) | 20nm, first UltraScale |
| **UltraScale+** | Kintex/Virtex UltraScale+ (XKU+/XVU+), Zynq UltraScale+ MPSoC/RFSOC | 16nm, PCIe Gen4, 100G Ethernet, HBM, RF data converters |
| Versal | Versal Prime/AI/Premium/HBM | ACAP: AI engines, NoC (network-on-chip), PCIe Gen5, DDR5 |
| Spartan-7 | XS7 | Low-cost 7-series, ideal for open-source toolchain experiments |
