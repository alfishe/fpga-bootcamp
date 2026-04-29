[← 11 Soft Cores And Soc Design Home](../README.md) · [← Riscv Cores Home](README.md) · [← Project Home](../../../README.md)

# NEORV32 — Best-Documented RISC-V Core

NEORV32 is a full SoC platform around a custom RV32 RISC-V core, with arguably the best documentation in open-source silicon — a 400+ page datasheet covering every peripheral and the CPU microarchitecture.

---

## Architecture

| Parameter | Value |
|---|---|
| **ISA** | RV32I + M + A + C + U (Zicsr, Zifencei) |
| **Pipeline** | 2-stage (fetch → execute) |
| **LUTs** | ~2,000–4,500 (depending on ISA/peripherals) |
| **fmax** | 150+ MHz on Artix-7, Cyclone V |
| **Debug** | JTAG via OpenOCD + GDB |
| **Bootloader** | Built-in, auto-loads from SPI flash |

## Built-In Peripherals (all optional)

| Peripheral | Function |
|---|---|
| **MTIME** | 64-bit RISC-V machine timer |
| **UART** ×2 | Primary console + secondary |
| **SPI** ×2 | Flash + general purpose |
| **TWI (I²C)** | Two-wire interface |
| **GPIO** | 64+ configurable pins |
| **PWM** | 4 channels |
| **WDT** | Watchdog timer |
| **TRNG** | True random number generator |
| **XIP** | Execute-in-place from SPI flash |
| **NEOLED** | Smart LED (WS2812) driver |

## What Makes It Unique

1. **No third-party libraries needed**: The entire SoC is self-contained in VHDL
2. **400+ page PDF datasheet**: Every register, every signal documented
3. **On-chip debugger**: JTAG OCD with hardware breakpoints, GDB support
4. **Bootloader in ROM**: Flashes itself from SPI without external programmer
5. **RISC-V compliance**: Passes official RISC-V architecture test suite

NEORV32 is the best choice when you want to **understand** your CPU, not just use it.

---

## Original Stub Description

Documentation for NEORV32 deep dive.

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [hard_processor_integration.md](../../02_architecture/soc/hard_processor_integration.md)
- [README.md](README.md)
