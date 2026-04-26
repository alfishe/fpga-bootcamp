[← Section Home](../README.md) · [← Project Home](../../README.md)

# 01-A — Intel / Altera (formerly Altera)

**Primary anchor: Cyclone V (DE10-Nano / MiSTer).** This is the recommended entry point for the FPGA knowledge base. Covers all Intel/Altera FPGA families with emphasis on the Cyclone V SoC used by the MiSTer project.

## Family Directories

Each family now has its own folder with a standalone README, matching the knowledge base structure used throughout this project.

| Directory | Coverage |
|---|---|
| [cyclone_v/](cyclone_v/README.md) | **★ Cyclone V** — anchor. SoC (dual Cortex-A9, HPS, AXI bridges, DE10-Nano/MiSTer) + FPGA-only variants (E/GX/GT, 25K–301K LEs) |
| [max_10/](max_10/README.md) | **MAX 10** — instant-on non-volatile flash, integrated ADC, 2K–50K LEs, dual-config safe update |
| [cyclone_10/](cyclone_10/README.md) | **Cyclone 10** — cost-optimized LP (60nm, legacy) & GX (20nm, 12G transceivers) |
| [arria_10/](arria_10/README.md) | **Arria 10** — 20nm mid-range, PCIe Gen3, 28G transceivers, IEEE 754 hard FP DSP, up to 1.15M LEs |
| [stratix_10/](stratix_10/README.md) | **Stratix 10** — 14nm Tri-Gate, HyperFlex routing, HBM2 (8 GB), 58G PAM4, quad Cortex-A53 SoC |
| [agilex/](agilex/README.md) | **Agilex 5/7/9** — chiplet (EMIB), Intel 7, AI tensor DSP (INT8/FP16/BF16), HBM2e, Gen5 PCIe |

## Quick Reference

| Family | Key Devices | Position |
|---|---|---|
| **Cyclone V SoC** | 5CSEA2/4/5/6/9, 5CSX | ★ Anchor. 28nm, up to 301K LEs, dual Cortex-A9 |
| Cyclone V E/GX/GT | 5CEA, 5CGX, 5CGT | FPGA-only variants, 28nm,lier transceivers up to 6G |
| MAX 10 | 10M02–10M50 | Instant-on non-volatile, integrated ADC, up to 50K LEs |
| Cyclone 10 LP | 10CL | Cost-optimized legacy, 60nm, up to 120K LEs |
| Cyclone 10 GX | 10CX | Budget 12G transceiver, 20nm, up to 220K LEs |
| Arria 10 | 10AX, 10AS (SoC) | Mid-range, 20nm, PCIe Gen3, 28G transceivers |
| Stratix 10 | 1SX (SoC), 1SG, 1ST | High-end, 14nm, HBM2, 58G PAM4 |
| Agilex 5 | A5E, A5D | Entry chiplet, Intel 7, Gen4 PCIe |
| Agilex 7 | A7F, A7I, A7M | High-perf chiplet, AI tensor DSP, HBM2e |
| Agilex 9 | A9R | RFSoC competitor, direct RF ADCs/DACs |
