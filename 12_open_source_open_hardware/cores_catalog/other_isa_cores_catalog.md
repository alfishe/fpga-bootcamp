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

## Multi-ISA Core Collections & Projects

Some projects provide implementations across multiple CPU architectures, often using unified design methodologies or targeting retro computing compatibility.

### MicroCore Labs (Ted Fried)

**Repository:** [MicroCoreLabs/Projects](https://github.com/MicroCoreLabs/Projects)

Ted Fried's MicroCore Labs provides microsequencer-based FPGA cores and emulator implementations for classic CPUs. The project spans multiple architectures with a focus on cycle-accurate emulation for retro computing and drop-in replacement applications.

| Core | Architecture | Implementation | Platform | Key Trait |
|------|-------------|----------------|----------|-----------|
| **MCL68** | Motorola 68000 | Microsequencer-based | FPGA (various) | Cycle-accurate 68000 emulator |
| **MCL65** | MOS 6502 | Microsequencer-based / C | FPGA / Software | Compact 6502 implementation |
| **MCL51** | Intel 8051 | Microsequencer-based | FPGA | 8051 microcontroller core |
| **MCL86** | Intel 8086/8088 | Microsequencer-based | FPGA | x86 real-mode compatible |
| **MCL86+** | Intel 8088 | Teensy 4.1 emulator | Teensy 4.1 | Drop-in 8088 replacement |
| **MCL86jr** | IBM PCjr Accelerator | Teensy 4.1 | Teensy 4.1 | Boosts PCjr to PC/AT speed |
| **MCLZ8** | Zilog Z80 | Teensy 4.1 emulator | Teensy 4.1 | Drop-in Z80 replacement |
| **MCL6809** | Motorola 6809E | Teensy 4.1 emulator | Teensy 4.1 | Drop-in 6809 replacement |
| **MCL64** | MOS 6510 (C64) | Teensy 4.1 emulator | Teensy 4.1 | Commodore 64 drop-in |
| **MCLR5** | RISC-V RV32I | Quad-issue superscalar | FPGA | High-performance RISC-V |

**Notable Projects:**

| Project | Description |
|---------|-------------|
| **XTMax** | 8-bit ISA card with Teensy 4.1 emulating RAM, ROM, and peripherals |
| **IBMPC_68000** | Emulates 68000 inside IBM PC using MCL86+ board (1981 "what-if" scenario) |
| **MCL65_Apple1** | Converts Apple II to Apple 1 by emulating BIOS PROMs and memory |
| **EPROM Emulator** | Teensy 4.0-based 27C512 EPROM emulator (up to 64KB) |
| **Wheelwriter** | FPGA/Arduino printer option for IBM Wheelwriter 5 |

**Strengths:**
- **Microsequencer architecture** — unified design approach across multiple ISAs
- **Drop-in replacements** — many cores designed as direct CPU replacements on real hardware
- **Cycle accuracy** — focuses on timing-accurate emulation for retro compatibility
- **Multi-platform** — both FPGA implementations and Teensy microcontroller emulators
- **Active development** — regularly updated with new cores and improvements

**Use Cases:**
- Retro computing hardware restoration and enhancement
- CPU accelerator cards for vintage systems
- Educational demonstrations of microsequencer-based CPU design
- Drop-in replacement for obsolete or hard-to-source CPUs

### Other Multi-ISA Collections

| Project | Architectures | Notes |
|---------|--------------|-------|
| **OpenCores** | 8051, Z80, 6502, MIPS, RISC-V, OR1K | Legacy repository with mixed-quality cores |
| **ZipCPU** | Custom (ZIP), 6502, Z80 | Dan Gisselquist's educational cores |
| **T80/T65** | Z80, 6502 | Widely used in MiSTer/MiST retro cores |

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

## Cross-References to Other CPU Core Catalogs

This catalog covers non-RISC-V and retro ISA cores. For a complete view of available FPGA CPU cores, see:

| Core Family | Catalog Article | Coverage |
|---|---|---|
| **RISC-V cores** | [RISC-V Cores Catalog](riscv_cores_catalog.md) | VexRiscv, PicoRV32, NEORV32, SERV, Ibex, Rocket, BOOM, CVA6, XiangShan |
| **Other open ISA cores** | This document | OpenRISC (mor1kx), LEON3/4 (SPARC), Microwatt (POWER), NEO430 (MSP430), Plasma (MIPS), ZPU, retro cores (Z80, 6502, 68000) |
| **Vendor soft processors** | [Vendor Soft Processors (Section 11)](../../11_soft_cores_and_soc_design/vendor_soft/README.md) | MicroBlaze/MicroBlaze-V (Xilinx/AMD), Nios II/Nios V (Intel/Altera) |
| **RISC-V deep dives** | [RISC-V Cores (Section 11)](../../11_soft_cores_and_soc_design/riscv_cores/README.md) | Detailed analysis of VexRiscv, PicoRV32, NEORV32, SERV, Ibex/CV32E40P, high-performance cores |
| **Non-RISC-V deep dives** | [Other ISA Cores (Section 11)](../../11_soft_cores_and_soc_design/other_isa/other_isa_cores.md) | Detailed analysis of mor1kx, LEON3/4, Microwatt, ZPU, Plasma, NEO430 |
| **SoC integration** | [SoC Design (Section 11)](../../11_soft_cores_and_soc_design/soc_design/README.md) | Bus matrices, memory maps, interrupt routing, DMA, multi-core coherency, Chipyard |
| **Peripheral cores** | [Peripheral Cores Catalog](peripheral_cores_catalog.md) | UART, SPI, I2C, GPIO, PWM, timers, Wishbone/AXI infrastructure cores |
| **MiSTer retro platform** | [MiSTer FPGA](../retro_computing/mister.md) | Retro computing cores using these soft CPUs (ZX Spectrum, C64, Amiga, etc.) |

---

## Cross-References

| Topic | Article |
|-------|---------|
| Non-RISC-V core deep dives | [Other ISA Cores](../../11_soft_cores_and_soc_design/other_isa/other_isa_cores.md) |
| RISC-V cores catalog | [RISC-V Cores Catalog](riscv_cores_catalog.md) |
| RISC-V core deep dives | [RISC-V Cores](../../11_soft_cores_and_soc_design/riscv_cores/README.md) |
| Multi-ISA collections | This document — Multi-ISA Core Collections section |
| MiSTer retro platform | [MiSTer](../retro_computing/mister.md) |
| Peripheral core collections | [Peripheral Cores Catalog](peripheral_cores_catalog.md) |
