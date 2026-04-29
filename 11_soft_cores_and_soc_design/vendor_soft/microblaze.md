[← 11 Soft Cores And Soc Design Home](../README.md) · [← Vendor Soft Home](README.md) · [← Project Home](../../../README.md)

# MicroBlaze — Xilinx's Soft Processor

MicroBlaze is Xilinx's proprietary 32-bit RISC soft core — free to use in Xilinx devices, deeply integrated with Vivado/Vitis, and the default soft CPU for Xilinx FPGAs.

---

## Architecture

| Parameter | Options |
|---|---|
| **ISA** | 32-bit RISC (custom, not RISC-V) |
| **Pipeline** | 3-stage (area-optimized) or 5-stage (performance) |
| **LUTs** | ~1,000 (microcontroller) to ~3,000 (Linux-capable MMU) |
| **fmax** | 200+ MHz on 7-series, 300+ MHz on Ultrascale+ |
| **MMU** | Optional (for Linux) |
| **FPU** | Optional (single or double precision) |
| **Debug** | XMD (Xilinx Microprocessor Debug) via JTAG |

## Variants

| Variant | Pipeline | LUTs | Features |
|---|---|---|---|
| **Microcontroller** | 3-stage | ~1,000 | Minimal, no cache, bare-metal |
| **Real-time** | 5-stage | ~2,000 | Instruction/data cache, FPU optional |
| **Linux** | 5-stage + MMU | ~3,000 | Virtual memory, runs Linux 4.x |

## AXI Integration

MicroBlaze uses AXI4 natively:
- **AXI4** for DDR memory (cache line fills)
- **AXI4-Stream** for FIFO-attached accelerators
- **AXI4-Lite** for GPIO, UART, I²C, SPI

This tight AXI coupling is why MicroBlaze + Vivado IP Integrator is the fastest path to a working SoC on Xilinx.

## MicroBlaze vs RISC-V on Xilinx

| Aspect | MicroBlaze | RISC-V (VexRiscv/etc.) |
|---|---|---|
| **Vivado integration** | ✅ Native IP, block design drag-and-drop | ❌ Manual integration |
| **Performance** | 200–300 MHz | 100–200 MHz |
| **Vendor lock-in** | Xilinx only | Any FPGA family |
| **License cost** | Free (Vivado license needed) | Free (open source) |
| **Toolchain** | Xilinx SDK / Vitis | GCC, LLVM (standard RISC-V) |

---

## Original Stub Description

Documentation for MicroBlaze deep dive.

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [hard_processor_integration.md](../../02_architecture/soc/hard_processor_integration.md)
- [README.md](README.md)
