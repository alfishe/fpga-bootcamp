[← Section Home](../README.md) · [← Project Home](../../README.md)

# 12-I — LiteX Ecosystem

LiteX is the most complete open-source SoC builder for FPGAs — a Python/Migen framework that generates full systems with CPU, memory controller, Ethernet, PCIe, SATA, and SD card support with a single config file. This sub-section covers the framework and its core library.

## Index

| File | Topic |
|---|---|
| [litex_overview.md](litex_overview.md) | LiteX deep dive: Migen FHDL, Python SoC builder API, Wishbone bus architecture, auto-generated CSR/memory maps, CPU options (VexRiscv, PicoRV32, Rocket, Microwatt, SERV...), BIOS boot flow, Linux on LiteX, Verilator simulation, 50+ supported boards |
| [litex_core_ecosystem.md](litex_core_ecosystem.md) | Core ecosystem: **LiteDRAM** (auto-calibrating DDR/SDRAM, compatibility matrix), **LiteEth** (Ethernet MAC + hardware UDP/IP), **LitePCIe** (endpoint + DMA), **LiteSATA**, **LiteSDCard**, **LiteSPI**, **LiteICLink**, **LiteScope** (logic analyzer) — per-core architecture, resource usage, integration examples |
