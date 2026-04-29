[← 06 Ip And Cores Home](../README.md) · [← Vendor Ip Home](README.md) · [← Project Home](../../../README.md)

# Gowin IP Catalog

Gowin EDA includes a built-in IP core generator with a limited but growing catalog. While smaller than Xilinx/Intel offerings, it covers essential functions for Gowin's target markets (edge computing, industrial, consumer).

---

## IP Generator Overview

**Tool:** Gowin EDA → IP Core Generator (standalone window)
**Interface:** Wizards for each IP with preview and configuration
**Output:** Verilog/VHDL wrapper files + placement constraints

---

## Available IP Categories

| Category | IP Blocks | Notes |
|---|---|---|
| **Clocking** | PLL, DLL, OSC | Easy wizard, critical for GW1N/GW2A timing |
| **Memory** | SDRAM Controller, HyperRAM, PSRAM, SPI Flash Controller | HyperRAM is Gowin's standout — fast, low-pin-count memory IP |
| **Bus Interfaces** | I2C, SPI, UART, I2S | Standard peripherals |
| **Video** | DVI TX (TMDS), LVDS LCD, Camera Interface | DVI TX useful for retro computing, HMI |
| **DSP** | FIR, FFT, DDS, Cordic, Multiplier | Growing DSP catalog |
| **Processor** | PicoRV32 RISC-V, Gowin EMCU (8051) | PicoRV32 is the recommended soft CPU |
| **Connectivity** | USB 2.0 Device, Ethernet MAC (10/100) | USB is a differentiator vs Lattice low-end |
| **Security** | AES, SHA, TRNG | Useful for IoT/security applications |

---

## Strengths

- **HyperRAM controller** — excellent for low-pin-count external RAM (12 pins for 8 MB)
- **USB 2.0 device** — rare in this price tier
- **Built-in PicoRV32** — RISC-V soft core directly from IP generator

---

## Limitations

- **No AXI interconnect** — use hand-coded Wishbone or simple bus
- **No DDR3/DDR4 controller** — SDRAM/HyperRAM only
- **No PCIe** — not relevant for Gowin's market, but worth noting
- **Catalog smaller than Xilinx/Intel** — but adequate for Gowin's use case

---

## References

- Gowin EDA User Guide (IP Generation section)
- Gowin IP Core Generator User Guide
