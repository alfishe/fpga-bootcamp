[← 11 Soft Cores And Soc Design Home](../README.md) · [← Vendor Soft Home](README.md) · [← Project Home](../../../README.md)

# Nios II/V — Intel's Soft Processor Family

Intel's Nios II is the legacy 32-bit RISC soft core for Intel FPGAs, while Nios V is its RISC-V-based successor — covering the Intel soft CPU ecosystem.

---

## Nios II Variants

| Variant | Pipeline | LUTs | fmax | DMIPS/MHz | Use |
|---|---|---|---|---|---|
| **Nios II/e** (Economy) | 1-stage (state machine) | ~600–700 | 200 MHz | ~0.15 | Smallest, slowest, debug console |
| **Nios II/s** (Standard) | 5-stage, static branch prediction | ~1,200–1,400 | 180 MHz | ~0.74 | Balanced, most common |
| **Nios II/f** (Fast) | 6-stage, dynamic branch prediction | ~1,400–1,800 | 200+ MHz | ~1.17 | Highest performance |

## Nios V — RISC-V Transition

| Variant | ISA | LUTs | fmax | Key Trait |
|---|---|---|---|---|
| **Nios V/m** (Microcontroller) | RV32IMC | ~1,200 | 150+ MHz | RISC-V, smallest, bare-metal |
| **Nios V/g** (General) | RV32IMAFDC | ~5,000 | 150+ MHz | Linux-capable, MMU, FPU |

## Intel vs Open RISC-V

| Aspect | Nios II | Nios V | Open RISC-V (VexRiscv) |
|---|---|---|---|
| **Quartus integration** | ✅ Native Qsys/Platform Designer | ✅ Native | ❌ Manual |
| **Avalon-MM** | ✅ Native | ✅ Native | ❌ Needs bridge |
| **License** | Free (Quartus license) | Free (Quartus license) | Free (open source) |
| **Cross-vendor** | Intel only | Intel only | Any FPGA family |
| **Debug** | ✅ SignalTap + Nios II SBT | ✅ SignalTap + Ashling RiscFree | 🟡 OpenOCD + GDB |

## When to Use Nios vs RISC-V

| Scenario | Choice |
|---|---|
| I'm in Quartus, want fastest SoC integration | **Nios II/f** — drag-and-drop in Platform Designer |
| I'm future-proofing for Intel RISC-V transition | **Nios V/m** — same Intel tooling, RISC-V ISA |
| I need cross-vendor portability | **Open RISC-V** (VexRiscv) — same core on Xilinx, Intel, Lattice |
| I have an existing Nios II codebase | **Stay on Nios II** — Nios V is new, toolchain maturing |

---

## Original Stub Description

Documentation for Nios II/V deep dive.

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [hard_processor_integration.md](../../02_architecture/soc/hard_processor_integration.md)
- [README.md](README.md)
