[← 11 Soft Cores And Soc Design Home](../README.md) · [← Riscv Cores Home](README.md) · [← Project Home](../../../README.md)

# SERV — World's Smallest RISC-V

SERV (SErial RISC-V) is a bit-serial RV32I implementation — it processes one bit per cycle, achieving a fully functional 32-bit RISC-V core in as few as ~125 LUTs on iCE40.

---

## Architecture

| Parameter | Value |
|---|---|
| **ISA** | RV32I (Zicsr, Zifencei) |
| **Pipeline** | None (bit-serial state machine) |
| **LUTs** | ~125 (minimal) to ~400 (with extensions) |
| **fmax** | ~50 MHz on iCE40, ~100 MHz on Artix-7 |
| **CPI** | ~32–64 cycles per instruction (1 bit per cycle × 32-bit operations) |
| **Performance** | ~1.5 MIPS at 50 MHz (DMIPS/MHz ~0.02) |

## How Bit-Serial Works

SERV uses a **1-bit datapath** — instead of 32 parallel wires for the ALU, it processes each instruction one bit at a time:

```
Traditional CPU:  ADD r1, r2, r3   → 32 bits in parallel, 1 cycle
SERV:              ADD r1, r2, r3   → 1 bit per cycle × 32 bits = 32+ cycles
```

The entire register file, ALU, and memory interface are 1-bit wide — the state machine steps through each bit position.

## Use Cases

| Scenario | Why SERV |
|---|---|
| **FPGA where every LUT counts** | ~125 LUTs vs ~750 for PicoRV32 |
| **Configuration/management CPU** | Slow register reads/writes — speed doesn't matter |
| **Test pattern generator** | Sequential state machine with RISC-V programmability |
| **Redundant monitoring core** | Use 10× SERVs for checker redundancy vs 1× small core |
| **Educational** | Simplest possible RISC-V to study |

## Reality Check

SERV runs ~50× slower than PicoRV32. It's not a general-purpose CPU — it's for cases where your FPGA has \u003c500 LUTs free and you need any processor at all.

---

## Original Stub Description

SERV: bit-serial RV32I, world's smallest RISC-V (~125 LUTs on iCE40), 1 bit per cycle, when footprint is everything

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
