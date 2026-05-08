[← 12 Open Source Open Hardware Home](../README.md) · [← Cores Catalog Home](README.md) · [← Project Home](../../../README.md)]

# Non-RISC-V Core Catalog

Not every open FPGA processor is RISC-V. This catalog covers open-source soft cores implementing other ISAs — from retro (Z80, 6502, 68000) to SPARC (LEON), POWER (Microwatt), and experimental architectures. For deep technical coverage of the modern/industrial-grade cores, see [Non-RISC-V Soft Cores](../../../11_soft_cores_and_soc_design/other_isa/other_isa_cores.md).

---

## Modern / Industrial-Grade Cores

| Core | ISA | Bits | LUTs | fMAX | Linux | License | Language | FPGA Verified | Key Trait |
|------|-----|------|------|------|-------|---------|----------|--------------|-----------|
| **mor1kx** | OpenRISC 1000 | 32 | 2,500–4,000 | 150+ MHz | ✅ 4.x | LGPL | Verilog | ECP5, Artix-7 | Mature GCC, Linux |
| **LEON3** | SPARC V8 | 32 | 15,000+ | 100+ MHz | ✅ | GPL + commercial | VHDL | Kintex-7 | Fault-tolerant, ESA |
| **LEON4** | SPARC V8 | 32 | 25,000+ | 150+ MHz | ✅ | GPL + commercial | VHDL | Kintex-7 | Multi-core LEON3 |
| **Microwatt** | POWER | 64 | 20,000+ | 50+ MHz | ✅ ppc64le | Apache 2.0 | VHDL | Artix-7 | IBM POWER, Linux |
| **NEO430** | MSP430 | 16 | 1,500–2,500 | 100+ MHz | ❌ | BSD-3 | VHDL | iCE40, ECP5 | 16-bit, great docs |
| **Plasma** | MIPS I | 32 | 2,000–3,000 | 100+ MHz | ❌ | MIT | VHDL | Artix-7 | Educational MIPS |
| **ZPU** | Custom stack | 32 | 500–1,000 | 100+ MHz | ❌ | BSD | VHDL | iCE40, ECP5 | Smallest 32-bit core |

### Selection Guide — Modern Cores

| You Need... | Choose | Because |
|-------------|--------|---------|
| Space-qualified processor | **LEON3/4** | ESA heritage, EDAC, TMR, flight-proven |
| 64-bit POWER on FPGA | **Microwatt** | Mainline Linux ppc64le, IBM-supported |
| Linux on non-RISC-V | **mor1kx** | Most mature non-RV Linux toolchain |
| Smallest 32-bit CPU | **ZPU** | ~500 LUTs, GCC toolchain |
| 16-bit ultra-low-power | **NEO430** | MSP430 compat, built-in peripherals |
| Simple educational core | **Plasma** | Clean MIPS I, MIT license |

---

## Retro ISA Soft Cores

Cycle-accurate and functionally-accurate soft implementations of classic CPUs, primarily used in MiSTer, MiST, and other retro computing platforms.

### 8-Bit Era

| Core | Original CPU | Accuracy | LUTs | Platforms | Notable Usage |
|------|-------------|----------|------|-----------|---------------|
| **T80** | Zilog Z80 | Cycle-accurate | ~2,000 | MiSTer, MiST, ZX-Uno | ZX Spectrum, MSX, CPC cores |
| **T65** | MOS 6502 | Cycle-accurate | ~1,500 | MiSTer, FPGA Arcade | C64, Apple II, NES, Atari |
| **6809** | Motorola 6809 | Cycle-accurate | ~2,500 | MiSTer | Vectrex, CoCo, Dragon |
| **8088** | Intel 8088 | Functional | ~3,000 | MiSTer | PC/XT clone |
| **AVR8** | Atmel AVR | Functional | ~2,000 | Various | Arduino-compatible soft core |

### 16/32-Bit Era

| Core | Original CPU | Accuracy | LUTs | Platforms | Notable Usage |
|------|-------------|----------|------|-----------|---------------|
| **fx68k** | Motorola 68000 | Cycle-accurate | ~5,000 | MiSTer, MiST | Amiga, Atari ST, Mega Drive |
| **ao68000** | Motorola 68000 | Functional | ~4,000 | OpenCores | Wishbone-compatible, SoC use |
| **TG68** | Motorola 68000 | Functional | ~3,500 | MiSTer, MiST | Minimig Amiga core |
| **68ksec** | Motorola 68020+ | Functional | ~8,000 | MiSTer | 68020/030 acceleration |
| **T11** | DEC PDP-11 | Functional | ~3,000 | Custom | PDP-11 recreation |

### ARM

| Core | Original CPU | Accuracy | LUTs | Notes |
|------|-------------|----------|------|-------|
| **arm_hdl** | ARMv4T (ARM7TDMI) | Functional | ~10,000 | GBA, ARM7TDMI-compatible |
| **amber** | ARMv2a (ARM2/3) | Functional | ~4,000 | OpenCores, ARM2-compatible |

---

## Core Quality Indicators

When evaluating a non-RISC-V core for production use, check:

| Indicator | mor1kx | LEON3 | Microwatt | ZPU | NEO430 | Plasma |
|-----------|--------|-------|-----------|-----|--------|--------|
| **Linux support** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **GCC toolchain** | ✅ | ✅ | ✅ | ✅ | ✅ (MSP430 GCC) | ✅ |
| **Active maintenance** | Medium | High (Gaisler) | Medium | Low | Medium | Low |
| **FPGA-verified** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Formal verification** | Partial | Extensive | Partial | None | None | None |
| **Documentation quality** | Good | Excellent | Good | Poor | Excellent | Fair |
| **Safety certification** | ❌ | ✅ (space) | ❌ | ❌ | ❌ | ❌ |

---

## Toolchain Quick Reference

| Core | Compiler | Debugger | Build System | Simulation |
|------|----------|----------|-------------|-----------|
| **mor1kx** | `or1k-elf-gcc` | `or1k-elf-gdb` | Make | Verilator, Icarus |
| **LEON3** | `sparc-elf-gcc` / BCC | `sparc-elf-gdb` | GRLIB Make | ModelSim, GHDL |
| **Microwatt** | `powerpc64le-linux-gnu-gcc` | `powerpc64le-linux-gnu-gdb` | Make | Verilator, GHDL |
| **ZPU** | `zpu-elf-gcc` | — | Custom | Icarus |
| **NEO430** | `msp430-elf-gcc` | `msp430-elf-gdb` | NEO430 Makefile | GHDL |
| **Plasma** | `mips-elf-gcc` | — | Custom | ModelSim |

---

## Cross-References

| Topic | Article |
|-------|---------|
| Non-RISC-V core deep dives | [Other ISA Cores](../../11_soft_cores_and_soc_design/other_isa/other_isa_cores.md) |
| RISC-V cores catalog | [RISC-V Cores Catalog](riscv_cores_catalog.md) |
| RISC-V core deep dives | [RISC-V Cores](../../11_soft_cores_and_soc_design/riscv_cores/README.md) |
| MiSTer retro platform | [MiSTer](../retro_computing/mister.md) |
| Peripheral core collections | [Peripheral Cores Catalog](peripheral_cores_catalog.md) |
