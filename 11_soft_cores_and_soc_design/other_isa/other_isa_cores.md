[← 11 Soft Cores And Soc Design Home](../README.md) · [← Other ISA Home](README.md) · [← Project Home](../../../README.md)

# Non-RISC-V Soft Cores — OpenRISC, SPARC, POWER, MIPS, MSP430, ZPU

While RISC-V dominates new soft core development, several mature non-RISC-V architectures remain relevant for FPGA — each with unique advantages and deep toolchain history. The LEON3/4 (SPARC V8) is the only ESA-qualified processor for space applications. The mor1kx (OpenRISC) offers the most mature Linux-capable non-RISC-V option. The Microwatt brings IBM's POWER ISA to the FPGA world. And the ZPU holds the record for the smallest FPGA CPU. This article provides deep technical coverage of each core: architecture, toolchain, FPGA resource requirements, Linux support, and when to choose each one.

> [!NOTE]
> For RISC-V cores, see [RISC-V Cores](../riscv_cores/README.md). For the full catalog including retro ISA soft cores, see [Non-RISC-V Core Catalog](../../12_open_source_open_hardware/cores_catalog/other_isa_cores_catalog.md).

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

---

## mor1kx — OpenRISC 1000

The mor1kx is the reference implementation of the OpenRISC 1000 (OR1K) architecture. It is the most mature non-RISC-V Linux-capable soft core, with a complete GCC/binutils toolchain and mainline Linux kernel support.

### Architecture

- **Pipeline**: 4-stage (classic) or 6-stage (multicycle) configurable
- **ISA**: OpenRISC 1000 (ORBIS32), 32-bit, fixed 32-bit instructions
- **Features**: MMU (Linux-capable), optional FPU, optional cache (4–64 KB)
- **Bus**: Wishbone revB4

### Configurations

| Variant | Pipeline | Cache | MMU | FPU | LUTs | Use |
|---|---|---|---|---|---|---|
| **or1200_compat** | 4-stage | Optional | Yes | No | ~2,500 | Legacy compatible |
| **mor1kx_simple** | 4-stage | No | No | No | ~1,800 | Minimal bare-metal |
| **mor1kx_cappuccino** | 6-stage | Yes | Yes | Optional | ~4,000 | Linux-capable with cache |

### Toolchain

| Component | Status | Notes |
|---|---|---|
| **GCC** | ✅ or1k-elf / or1k-linux | Full C/C++ support since GCC 4.9 |
| **binutils** | ✅ | Assembler, linker, objdump |
| **Linux kernel** | ✅ Mainline since 3.1 | Requires MMU variant |
| **newlib** | ✅ | Bare-metal C library |
| **Buildroot** | ✅ | Complete Linux root filesystem |
| **OpenCores** | ✅ | Reference SoC (orpsoc) |

### When to Choose mor1kx

| Scenario | Why mor1kx |
|---|---|
| Linux on FPGA without RISC-V | Most mature non-RV Linux path — stable kernel, full toolchain |
| OpenRISC ecosystem requirement | The reference OR1K implementation |
| Wishbone-based SoC | Native Wishbone bus — integrates with existing WB peripherals |

---

## LEON3/4 — SPARC V8 (ESA-Qualified)

The LEON3 and LEON4 are SPARC V8 processors developed by Cobham Gaisler (formerly Gaisler Research) under contract from the European Space Agency (ESA). They are the **only** ESA-qualified soft processors available for space applications.

### Architecture

- **ISA**: SPARC V8 (32-bit), 72 standard instructions + custom instructions
- **Pipeline**: LEON3 = 7-stage, LEON4 = 7-stage (improved branch prediction)
- **Cache**: Configurable I/D caches (1–256 KB each)
- **MMU**: Optional (required for Linux)
- **FPU**: Optional GRFPU (high-performance) or Meiko FPU
- **Bus**: AMBA AHB/APB

### LEON3 vs LEON4

| Feature | LEON3 | LEON4 |
|---|---|---|
| **Pipeline depth** | 7-stage | 7-stage (improved) |
| **Multi-core** | Up to 4 cores | Up to 16 cores |
| **Branch prediction** | Static | Dynamic (2-bit saturating) |
| **Performance** | 1.0 Dhrystone MIPS/MHz | 1.4 Dhrystone MIPS/MHz |
| **LUTs (1 core)** | ~15,000 | ~25,000 |
| **License** | GPL + commercial | Commercial only |

### GRLIB IP Library

The LEON cores are distributed as part of the GRLIB IP library — a comprehensive collection of space-qualified IP:

| IP Block | Function |
|---|---|
| **LEON3/4** | SPARC V8 processor |
| **GRFPU** | Floating-point unit |
| **GRETH** | 10/100/1000 Ethernet MAC |
| **GRSPW** | SpaceWire (IEEE 1355) |
| **GRGPIO** | General-purpose I/O |
| **GRTIMER** | Timer unit |
| **GRIRQMP** | Interrupt controller |
| **GRMEMCTRL** | Memory controller (SDRAM, DDR2) |
| **GRPCI** | PCI host bridge |
| **GRUSB** | USB 2.0 host |

### Licensing

| License | Use Case | Cost |
|---|---|---|
| **GPL** | Open-source evaluation, non-commercial | Free |
| **Cobham Commercial** | Commercial products without GPL obligations | Paid |
| **Cobham Radiation-Hardened** | Space-qualified, flight-proven versions | Paid (higher) |

### When to Choose LEON3/4

| Scenario | Why LEON |
|---|---|
| Space application (ESA-qualified) | The only qualified soft processor for European space missions |
| Fault-tolerant design required | GRLIB includes EDAC, scrubbing, TMR options |
| SPARC V8 software compatibility | Existing SPARC codebase (Solaris, VxWorks ports) |
| Multi-core soft processor | LEON4 supports up to 16 cores on a single FPGA |

---

## Microwatt — POWER9 on FPGA

Microwatt is an open-source 64-bit POWER ISA processor for FPGAs, developed with support from IBM and the OpenPOWER Foundation. It targets the POWER9 Little-Endian ISA and runs mainline Linux.

### Architecture

- **ISA**: POWER9 LE (64-bit), subset of full POWER9
- **Pipeline**: 4-stage, simple in-order
- **Cache**: L1 I/D caches (configurable)
- **MMU**: Simple, Linux-capable
- **Bus**: Wishbone
- **Language**: VHDL

### Toolchain

| Component | Status | Notes |
|---|---|---|
| **GCC** | ✅ powerpc64le-linux | Standard PPC64LE toolchain |
| **Linux kernel** | ✅ Mainline | Boots with minimal config |
| **Microwatt SoC** | ✅ | Arty A7 reference design |

### When to Choose Microwatt

| Scenario | Why Microwatt |
|---|---|
| POWER ISA exploration | Only open-source POWER core — educational and research |
| IBM ecosystem integration | Compatible with IBM toolchain and software |
| 64-bit Linux on FPGA (non-RISC-V) | Alternative to 64-bit RISC-V for POWER-centric teams |

---

## ZPU — The Smallest FPGA CPU

The ZPU is a stack-based 32-bit processor designed to be the smallest possible FPGA CPU. It executes a custom ISA where all operations are stack-based (push, pop, add, etc.) rather than register-based.

### Architecture

- **ISA**: Custom stack-based (32-bit), ~15 instructions in the minimal subset
- **Pipeline**: None (single-cycle microcoded)
- **Registers**: No general-purpose registers — stack only
- **Bus**: Wishbone
- **Language**: VHDL

### Resource Requirements

| Configuration | LUTs | fmax | Memory | Use |
|---|---|---|---|---|
| **ZPU Tiny** | ~500 | 50+ MHz | Minimal | Smallest possible CPU |
| **ZPU Small** | ~800 | 80+ MHz | 4 KB BRAM | Basic control tasks |
| **ZPU Medium** | ~1,200 | 100+ MHz | 16 KB BRAM | Moderate processing |

### Toolchain

| Component | Status |
|---|---|
| **zpu-gcc** | ✅ GCC port (C/C++) |
| **zpu-elf-newlib** | ✅ Bare-metal C library |
| **zpu-as** | ✅ Assembler |
| **Linux** | ❌ No MMU |

### When to Choose ZPU

| Scenario | Why ZPU |
|---|---|
| Need a CPU in <1K LUTs | The smallest 32-bit FPGA CPU available |
| Simple control logic | Replace FSM with programmable CPU |
| Boot ROM management | Tiny footprint leaves room for boot code |

---

## NEO430 — MSP430 for FPGA

The NEO430 is a 16-bit MSP430-compatible soft core with exceptional documentation — second only to NEORV32 in documentation quality.

### Architecture

- **ISA**: MSP430 (16-bit), 27 core instructions + 24 emulated
- **Pipeline**: 1–3 cycles per instruction
- **Registers**: 16 registers (R0–R15), R0=PC, R1=SP, R2=SR
- **Memory**: 16-bit Von Neumann, byte-addressable
- **Peripherals**: Built-in UART, SPI, I2C, timer, GPIO
- **Bus**: Custom internal bus

### Key Features

- Ultra-low power design philosophy (clock gating throughout)
- Complete self-checking testbench included
- No vendor-specific primitives — fully portable VHDL
- Comprehensive user manual (300+ pages)

### When to Choose NEO430

| Scenario | Why NEO430 |
|---|---|
| 16-bit ultra-low-power core | MSP430 compatibility + FPGA flexibility |
| Best-in-class documentation | Easiest non-RISC-V core to learn and integrate |
| Sensor interface processing | 16-bit ADC/DAC processing with MSP430 software compatibility |

---

## Plasma — Educational MIPS

The Plasma core implements the MIPS I instruction set — the architecture taught in most computer architecture courses (Patterson & Hennessy). It serves primarily as an educational platform.

### Architecture

- **ISA**: MIPS I (32-bit), subset of full MIPS
- **Pipeline**: 3-stage (fetch, decode, execute)
- **No MMU**: Bare-metal or RTOS only
- **Language**: VHDL

### When to Choose Plasma

| Scenario | Why Plasma |
|---|---|
| Teaching computer architecture | MIPS is the textbook ISA — students can trace every pipeline stage |
| Simple control processor | Small footprint, easy to understand and modify |

---

## Decision Guide

| I need... | Choose | Why |
|---|---|---|
| Linux on FPGA without RISC-V | **mor1kx** | Most mature non-RV Linux path |
| Space-qualified processor | **LEON3/4** | ESA-qualified, fault-tolerant |
| The smallest possible CPU | **ZPU** | ~500 LUTs |
| 64-bit POWER on FPGA | **Microwatt** | IBM-supported, Linux-capable |
| 16-bit ultra-low-power core | **NEO430** | MSP430 compatibility, great docs |
| Educational MIPS | **Plasma** | Textbook ISA, easy to understand |

---

## References

| Source | Description |
|---|---|
| [OpenRISC mor1kx](https://github.com/openrisc/mor1kx) | mor1kx source and documentation |
| [Cobham Gaisler LEON3](https://www.gaisler.com/index.php/products/processors/leon3) | LEON3/4 product page and GRLIB |
| [Microwatt](https://github.com/antonblanchard/microwatt) | POWER9 FPGA core |
| [ZPU](https://opencores.org/projects/zpu) | ZPU stack-based CPU |
| [NEO430](https://github.com/stnolting/neo430) | MSP430-compatible FPGA core |
| [Plasma](https://opencores.org/projects/plasma) | MIPS I FPGA core |
| [RISC-V Cores](../riscv_cores/README.md) | RISC-V alternatives |
| [Non-RISC-V Core Catalog](../../12_open_source_open_hardware/cores_catalog/other_isa_cores_catalog.md) | Full catalog including retro ISA soft cores |
