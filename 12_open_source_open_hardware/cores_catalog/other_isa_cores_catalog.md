[← 12 Open Source Open Hardware Home](../README.md) · [← Cores Catalog Home](README.md) · [← Project Home](../../../README.md)

# Non-RISC-V Core Catalog

Not every open FPGA processor is RISC-V. This catalog covers open-source soft cores implementing other ISAs — from retro (Z80, 6502, 68000) to SPARC (LEON), POWER (Microwatt), and experimental architectures. For deep technical coverage of the modern/industrial-grade cores, see [Non-RISC-V Soft Cores](../../../11_soft_cores_and_soc_design/other_isa/other_isa_cores.md).

---

## Modern / Industrial-Grade Cores

| Core | ISA | LUTs | fmax | FPGA Verified | Language | License | Key Trait |
|---|---|---|---|---|---|---|---|
| **mor1kx** | OpenRISC 1000 (OR1K) | ~2,500–4,000 | 150+ MHz | ECP5, Artix-7 | Verilog | LGPL | Linux-capable, mature GCC toolchain |
| **LEON3** | SPARC V8 | ~15,000+ | 100+ MHz | Kintex-7, Virtex | VHDL | GPL + commercial | ESA-qualified, GRLIB ecosystem, fault-tolerant |
| **LEON4** | SPARC V8 | ~25,000+ | 150+ MHz | Kintex-7, Virtex | VHDL | Commercial | Multi-core (up to 16), dynamic branch prediction |
| **Microwatt** | POWER9 (64-bit) | ~20,000+ | 50+ MHz | Artix-7 (Arty) | VHDL | Apache 2.0 | IBM POWER ISA, mainline Linux ppc64le |
| **NEO430** | MSP430-compatible | ~1,500–2,500 | 100+ MHz | iCE40, ECP5 | VHDL | BSD-3-Clause | 16-bit, ultra-low power, best docs after NEORV32 |
| **Plasma** | MIPS I | ~2,000–3,000 | 100+ MHz | Artix-7 | VHDL | MIT | Educational MIPS, RTOS support |
| **ZPU** | Custom lightweight | ~500–1,000 | 100+ MHz | iCE40, ECP5 | VHDL | BSD | Minimal stack-based, GCC toolchain |

### Quick Selection

| I need... | Core | Why |
|---|---|---|
| Linux on FPGA without RISC-V | **mor1kx** | Most mature non-RV Linux path |
| Space-qualified processor | **LEON3/4** | ESA-qualified, GRLIB fault-tolerance |
| The smallest possible CPU | **ZPU** | ~500 LUTs, stack-based |
| 64-bit POWER on FPGA | **Microwatt** | IBM-supported, Linux-capable |
| 16-bit ultra-low-power core | **NEO430** | MSP430 compatibility, excellent docs |
| Educational MIPS | **Plasma** | Textbook ISA, simple pipeline |

---

## Retro ISA Soft Cores

For vintage computing enthusiasts and preservation: cycle-accurate soft implementations of classic CPUs. These cores power retro computing platforms like MiSTer, MiST, and FPGA Arcade.

| Core | Original CPU | Target Platforms | Accuracy | Language | License | Notes |
|---|---|---|---|---|---|---|
| **T80** | Zilog Z80 | MiSTer, MiST, ZX-Uno | Cycle-accurate | VHDL | BSD | Most popular Z80 FPGA core, used in Spectrum/MSX/CPC cores |
| **fx68k** | Motorola 68000 | MiSTer (Minimig), MiST | Cycle-accurate | Verilog | GPL | Amiga/Atari ST cores, microcode-level accuracy |
| **T65** | MOS 6502 | MiSTer, FPGA Arcade | Cycle-accurate | VHDL | GPL | C64, Apple II, NES cores use variants |
| **ao68000** | Motorola 68000 | OpenCores, MiSTer | Instruction-accurate | Verilog | GPL | Wishbone-compatible, used in some FPGA SoCs |
| **TG68** | Motorola 68000/020 | MiSTer, MiST | Cycle-accurate | Verilog | GPL | Supports 68000 + partial 68020 extensions |
| **M68000i** | Motorola 68000 | Various | Instruction-accurate | Verilog | MIT | Compact implementation, good for small FPGAs |
| **65C02** | WDC 65C02 | Apple IIc cores | Cycle-accurate | VHDL | Various | CMOS variant with additional instructions |
| **6809** | Motorola 6809 | CoCo, Dragon cores | Cycle-accurate | VHDL | GPL | TRS-80 Color Computer, Dragon 32/64 |
| **S80186** | Intel 80186 | PC XT cores | Instruction-accurate | Verilog | MIT | IBM PC/XT compatible |

### Retro Core Resource Requirements

| Core | Target CPU | LUTs (typical) | BRAM | Clock |
|---|---|---|---|---|
| T80 | Z80 | ~2,000 | 2 | 50 MHz |
| fx68k | 68000 | ~8,000 | 4 | 50 MHz |
| T65 | 6502 | ~1,500 | 1 | 50 MHz |
| ao68000 | 68000 | ~5,000 | 2 | 25 MHz |

---

## When to Choose a Non-RISC-V Core

| Scenario | Recommendation | Rationale |
|---|---|---|
| I need a tiny processor (<1K LUTs) | **ZPU** or **NEO430** | ZPU is smallest; NEO430 has better docs |
| I want a proven, fault-tolerant space-grade design | **LEON3/4** (SPARC, ESA-qualified) | Only ESA-qualified soft processor |
| I'm building an Amiga/ST retro core | **fx68k** for CPU, **T80** for secondary | Cycle-accurate, proven in MiSTer |
| I want Linux on FPGA without RISC-V | **mor1kx** (OpenRISC) — most mature non-RISC-V Linux option | Stable GCC, mainline Linux since 3.1 |
| I'm curious about POWER on FPGA | **Microwatt** — educational, IBM-supported | Runs mainline Linux ppc64le |
| I need a 16-bit MCU replacement | **NEO430** — MSP430 compatibility, great docs | Drop-in for MSP430 code on FPGA |
| I'm teaching computer architecture | **Plasma** (MIPS I) | Textbook ISA, simple 3-stage pipeline |

---

## Cross-References

- [Non-RISC-V Soft Cores Deep Dive](../../../11_soft_cores_and_soc_design/other_isa/other_isa_cores.md) — Full technical coverage of mor1kx, LEON3/4, Microwatt, ZPU, NEO430, Plasma
- [RISC-V Cores Catalog](riscv_cores_catalog.md) — The dominant ISA for new soft core development
- [Peripheral Core Catalog](peripheral_cores_catalog.md) — Companion IP for building complete SoCs
- [MiSTer Platform](../retro_computing/mister.md) — Primary platform for retro ISA soft cores
