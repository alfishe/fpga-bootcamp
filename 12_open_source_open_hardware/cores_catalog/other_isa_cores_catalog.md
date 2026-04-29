[← 12 Open Source Open Hardware Home](../README.md) · [← Cores Catalog Home](README.md) · [← Project Home](../../../README.md)

# Non-RISC-V Core Catalog

Not every open FPGA processor is RISC-V. This catalog covers open-source soft cores implementing other ISAs — from retro (Z80, 6502, 68000) to SPARC (LEON), POWER (Microwatt), and experimental architectures.

---

## Modern / Industrial-Grade Cores

| Core | ISA | LUTs | fmax | FPGA Verified | Key Trait |
|---|---|---|---|---|---|
| **mor1kx** | OpenRISC 1000 (OR1K) | ~2,500–4,000 | 150+ MHz | ECP5, Artix-7 | Linux-capable, mature |
| **LEON3** | SPARC V8 | ~15,000+ | 100+ MHz | Kintex-7 | Fault-tolerant, GRLIB ecosystem |
| **Microwatt** | POWER9 (64-bit) | ~20,000+ | 50+ MHz | Artix-7 | IBM POWER ISA, VHDL, Linux-capable |
| **NEO430** | MSP430-compatible | ~1,500–2,500 | 100+ MHz | iCE40, ECP5 | 16-bit, ultra-low power, great docs |
| **Plasma** | MIPS I | ~2,000–3,000 | 100+ MHz | Artix-7 | Educational MIPS, RTOS support |
| **ZPU** | Custom lightweight | ~500–1,000 | 100+ MHz | iCE40, ECP5 | Minimal stack-based, GCC toolchain |

## Retro ISA Soft Cores

For vintage computing enthusiasts and preservation: cycle-accurate soft implementations of classic CPUs.

| Core | Original CPU | Target Platforms | Notes |
|---|---|---|---|
| **T80** | Zilog Z80 | MiSTer, MiST, ZX-Uno | Most popular Z80 FPGA core, used in Spectrum/MSX cores |
| **fx68k** | Motorola 68000 | MiSTer (Minimig), MiST | Cycle-accurate 68000, Amiga/Atari ST cores |
| **T65** | MOS 6502 | MiSTer, FPGA Arcade | C64, Apple II, NES cores use variants |
| **ao68000** | Motorola 68000 | OpenCores | Wishbone-compatible, used in some FPGA SoCs |
| **ZPU** | Custom stack CPU | General FPGA | Tiny footprint, GCC support via ZPU toolchain |

## When to Choose a Non-RISC-V Core

| Scenario | Recommendation |
|---|---|
| I need a tiny processor (\u003c1000 LUTs) | **ZPU** or **NEO430** |
| I want a proven, fault-tolerant space-grade design | **LEON3/4** (SPARC, ESA-qualified) |
| I'm building an Amiga/ST retro core | **fx68k** for CPU, **T80** for secondary |
| I want Linux on FPGA without RISC-V | **mor1kx** (OpenRISC) — most mature non-RISC-V Linux option |
| I'm curious about POWER on FPGA | **Microwatt** — educational, IBM-supported |

---

## Original Stub Description

Non-RISC-V inventory: OpenRISC (mor1kx), LEON3/4 (SPARC), Microwatt (POWER9), NEO430 (MSP430), Plasma (MIPS), ZPU, plus retro ISA soft cores (Z80, 6502, 68000) for vintage computing enthusiasts

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
- [hard_processor_integration.md](../../02_architecture/soc/hard_processor_integration.md)
