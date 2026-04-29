[← 12 Open Source Open Hardware Home](../README.md) · [← Cores Catalog Home](README.md) · [← Project Home](../../../README.md)

# RISC-V Core Catalog

A curated catalog of open-source RISC-V soft cores for FPGA deployment, organized by capability tier.

---

## Core Comparison Matrix

| Core | ISA | Pipeline | LUTs | fmax | FPGA Verified | Key Trait |
|---|---|---|---|---|---|---|
| **VexRiscv** | RV32IM[A][C] | 2–5 stage, configurable | ~1,200–3,000 | 200+ MHz | ECP5, Artix-7, Cyclone V | SpinalHDL, most configurable |
| **PicoRV32** | RV32IMC | 1 stage (multicycle) | ~750–2,000 | 150+ MHz | iCE40, ECP5, Artix-7 | Smallest, pure Verilog |
| **NEORV32** | RV32IM[A][C][U] | 2 stage | ~2,000–4,500 | 150+ MHz | Artix-7, Cyclone V | Best documentation, rich peripheral set |
| **Ibex** | RV32IMC | 2 stage | ~3,000–6,000 | 150+ MHz | Artix-7, Kintex-7 | lowRISC, OpenTitan RoT |
| **SERV** | RV32I | Bit-serial (1-bit ALU) | ~200–400 | 50 MHz | iCE40, ECP5, Artix-7 | World's smallest RV32 |
| **SweRV** | RV32IMC | 9 stage, dual-issue | ~5,000–8,000 | 600+ MHz (ASIC) | Limited FPGA | Western Digital, high perf |
| **Rocket** | RV64IMAFDC | 5 stage, in-order | ~15,000+ | 100+ MHz | Kintex-7, Zynq | Linux-capable, Chisel |
| **BOOM** | RV64IMAFDC | Out-of-order | ~30,000+ | 50+ MHz | Kintex-7 (large) | Superscalar, Chisel |
| **CVA6 (Ariane)** | RV64IMAFDC | 6 stage | ~25,000+ | 50+ MHz | Kintex-7, Genesys 2 | Linux-capable, OpenHW |

## Selection Guide

| Use Case | Recommended Core | Why |
|---|---|---|
| I need Linux on soft CPU | **Rocket** or **CVA6** | RV64 with MMU, FPU, supervisor mode |
| Bare-metal controller, low LUT budget | **VexRiscv** (minimal config) or **PicoRV32** | ~1K LUTs achievable |
| I want the best docs and onboard peripherals | **NEORV32** | 400+ page datasheet, UART/SPI/GPIO/MTIME built-in |
| I need security (RoT, trusted boot) | **Ibex** | Physically-aware, OpenTitan ecosystem verification |
| I'm LUT-starved (\u003c500 LUTs total) | **SERV** | 200 LUTs for full RV32I, but slow |
| I need high single-thread performance | **SweRV** | Dual-issue, 9-stage, but FPGA-friendly is limited |
| I want RISC-V + a rich peripheral ecosystem | **VexRiscv + LiteX** | LiteX wraps VexRiscv with DRAM/Ethernet/PCIe |

## Beyond This Catalog

- **Deep dives:** Individual core documentation in [Section 11 — Soft Cores](../../11_soft_cores_and_soc_design/riscv_cores/) — VexRiscv, PicoRV32, NEORV32, Ibex, SERV each get dedicated coverage.
- **SoC integration:** [LiteX overview](../litex/litex_overview.md) — how LiteX packages these cores into working SoCs.

---

## Original Stub Description

Documentation for Section 12 — RISC-V Core Catalog.

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
- [hard_processor_integration.md](../../02_architecture/soc/hard_processor_integration.md)
- [README.md](../../11_soft_cores_and_soc_design/riscv_cores/README.md)
