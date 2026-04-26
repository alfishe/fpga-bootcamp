[← Section Home](../README.md) · [← Project Home](../../README.md)

# 01-E — Microchip (formerly Microsemi/Actel)

Flash-based and anti-fuse FPGA specialist. Microchip's PolarFire and SmartFusion families offer low-power, radiation-tolerant, and SEU-immune options — with a hard RISC-V CPU ecosystem (Mi-V).

## Family Directories

| Directory | Coverage |
|---|---|
| [polarfire/](polarfire/README.md) | **PolarFire (28nm SONOS)** — FPGA-only (100K–482K LEs, 12.7G SERDES, PCIe Gen2) + **PolarFire SoC**: 5× hard RISC-V cores (4× U54 + E51, Linux-capable, 64-bit RV64IMAFDC). RT PolarFire (radiation-tolerant, >100 Krad). Instant-on <1 ms, SEU immune |
| [smartfusion2_igloo2/](smartfusion2_igloo2/README.md) | **SmartFusion2 & IGLOO2 (65nm flash)** — SmartFusion2: hard Cortex-M3 + 12-bit ADC + FIPS 140-2 crypto (anti-tamper, zeroization). IGLOO2: same fabric without MCU/analog |

## Quick Reference

| Family | Key Devices | Notes |
|---|---|---|
| **PolarFire** | MPF100/200/300/500 (non-SoC), MPFS (SoC with 5× RISC-V) | 28nm SONOS non-volatile, low power, SEU immune. PolarFire SoC: RISC-V hard cores |
| SmartFusion2 | M2S | Flash-based FPGA + ARM Cortex-M3, integrated ADCs |
| IGLOO2 | M2GL | Flash-based FPGA, simpler than SmartFusion2 |
| RT PolarFire | RTPF | Radiation-tolerant for space applications |
