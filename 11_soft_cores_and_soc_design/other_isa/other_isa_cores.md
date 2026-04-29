[← 11 Soft Cores And Soc Design Home](../README.md) · [← Other Isa Home](README.md) · [← Project Home](../../../README.md)

# Non-RISC-V Soft Cores — OpenRISC, SPARC, POWER, MIPS

While RISC-V dominates new soft core development, several mature non-RISC-V architectures remain relevant for FPGA — each with unique advantages and deep toolchain history.

---

## Core Comparison

| Core | ISA | LUTs | fmax | Linux | Language | Key Trait |
|---|---|---|---|---|---|---|
| **mor1kx** | OpenRISC 1000 | ~2,500–4,000 | 150+ MHz | ✅ | Verilog | Mature, GCC/binutils, Linux 4.x |
| **LEON3** | SPARC V8 | ~15,000+ | 100+ MHz | ✅ (RTEMS, Linux) | VHDL | ESA-qualified, GRLIB ecosystem, fault-tolerant |
| **LEON4** | SPARC V8 | ~25,000+ | 150+ MHz | ✅ | VHDL | Multi-core, faster LEON3 successor |
| **Microwatt** | POWER9 (64-bit) | ~20,000+ | 50+ MHz | ✅ | VHDL | IBM POWER ISA, Linux, educational |
| **Plasma** | MIPS I | ~2,000–3,000 | 100+ MHz | ❌ (RTOS) | VHDL | Educational MIPS, small |
| **ZPU** | Custom stack | ~500–1,000 | 100+ MHz | ❌ | VHDL | Smallest non-RV core, GCC toolchain |
| **NEO430** | MSP430 | ~1,500–2,500 | 100+ MHz | ❌ | VHDL | 16-bit, best docs after NEORV32 |

## When to Choose Non-RISC-V

| Scenario | Core | Why |
|---|---|---|
| I need a space-qualified FPGA processor | **LEON3/4** | ESA-qualified, GRLIB fault-tolerance (EDAC, scrubbing) |
| I want to learn POWER on FPGA | **Microwatt** | IBM-supported, runs mainline Linux ppc64le |
| I want the smallest possible FPGA CPU | **ZPU** | Stack-based, ~500 LUTs |
| I need a 16-bit ultra-low-power core | **NEO430** | MSP430 compatibility, excellent docs |

---

## Original Stub Description

Survey: **OpenRISC** (mor1kx), **LEON3/4** (SPARC V8, GPL + commercial dual license, ESA heritage), **Microwatt** (POWER9 subset, VHDL), **ZPU** (stack-based), **Plasma** (MIPS I), **NEO430** (MSP430 clone, excellent docs) — comparison: ISA, gate count, toolchain support, active maintenance

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
