[← 12 Open Source Open Hardware Home](../README.md) · [← Gpu Compute Home](README.md) · [← Project Home](../../../README.md)

# Open-Source GPU Cores

Soft GPU implementations ranging from educational proof-of-concepts to full-stack GPGPU platforms with OpenCL drivers.

---

## GPU Core Comparison

| GPU | ISA | Shader Cores | Clock (FPGA typical) | Driver Stack | FPGA Verified | Key Trait |
|---|---|---|---|---|---|---|
| **VeriGPU** | Custom (Verilog) | Configurable | ~50 MHz | Bare (memory-mapped) | ECP5, Artix-7 | Educational, pure Verilog, best to learn GPU architecture |
| **Vortex GPGPU** | RISC-V (custom ISA extension) | 1–32 cores | ~100 MHz | OpenCL 1.2 | Artix-7, Cyclone V | Full-stack: simulator, driver, FPGA — most complete open GPU |
| **Ventus GPGPU** | RISC-V (custom vector) | 1–8 warps | ~100 MHz | OpenCL | VCU118 (Virtex) | Tsinghua Univ., Chisel-generated, active research |
| **TinyGPU** | Custom minimal | 1 core | ~50 MHz | Bare | iCE40, ECP5 | Smallest, educational — fits in \u003c5K LUTs |
| **FGPU** | Custom (VHDL) | SIMD array | ~100 MHz | Bare | Artix-7 | Soft GPU with VGA output, memory controller |

## When to Use a Soft GPU

| Scenario | Recommendation |
|---|---|
| I want to learn GPU architecture | **VeriGPU** — clean Verilog, small, well-commented |
| I need OpenCL on FPGA without ARM | **Vortex** — the only option with a real OpenCL driver stack |
| I need the smallest possible GPU | **TinyGPU** — proof-of-concept, under 5K LUTs |
| I'm doing GPU architecture research | **Ventus** — Chisel-based, parameterized, academic |

## Reality Check

All FPGA soft GPUs are 10–100× slower than a modern iGPU. They're useful for:
- Learning GPU architecture internals
- Researching novel GPU ISA extensions
- Low-resolution embedded graphics (\u003c800×600)
- GPGPU exploration at small scale

For **production GPU acceleration**: use a hard ARM GPU (Zynq Ultrascale+ Mali) or a PCIe GPU connected to FPGA.

---

## Original Stub Description

**VeriGPU** (educational, Verilog GPU), **Vortex GPGPU** (RISC-V based, full-stack: OpenCL driver, simulator, FPGA), **Ventus GPGPU** (THU, Chisel, OpenCL), **TinyGPU** (minimal, educational), **FGPU** (soft GPU)

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
