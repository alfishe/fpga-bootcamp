[← 11 Soft Cores And Soc Design Home](../README.md) · [← Riscv Home](README.md) · [← Project Home](../../../README.md)

# RISC-V ISA — Base & Standard Extensions

A pragmatic reference for FPGA developers — what each RISC-V extension provides, how much it costs in LUTs, and when to enable it.

---

## Extensions at a Glance

| Extension | Name | Adds | LUT Cost | Enable When |
|---|---|---|---|---|
| **RV32I** | Base Integer | 40 instructions, 32 registers | Baseline | Always (mandatory) |
| **RV64I** | 64-bit Base | 64-bit registers, addw/subw/etc. | +30% over RV32I | Need \u003e4 GB addressing or 64-bit arithmetic |
| **M** | Multiply/Divide | mul, div, rem (signed/unsigned) | +300–1,500 LUTs | DSP, crypto, any math-heavy code |
| **A** | Atomic | lr/sc, amoswap/add/and/or/xor/min/max | +500–1,000 LUTs | Multi-core, shared memory synchronization |
| **F** | Single FP | 32-bit FPU, 32 FP registers | +2,000–4,000 LUTs | Sensor fusion, DSP with floating-point |
| **D** | Double FP | 64-bit FPU | +4,000–8,000 LUTs | Scientific computing, avoid on FPGA |
| **C** | Compressed | 16-bit instruction forms | +200–500 LUTs | Always (saves ~30% code size) |
| **B** | Bit Manipulation | clz, ctz, pcnt, rotate, bfp | +300–800 LUTs | Cryptography, networking, bit processing |
| **V** | Vector | Configurable-width SIMD | +5,000–50,000+ LUTs | ML/DSP acceleration, large FPGAs only |

## Instruction Formats

All RISC-V instructions are 32-bit (or 16-bit with C extension), with 6 formats: R, I, S, B, U, J.

## CSRs — Control and Status Registers

| CSR | Purpose | FPGA Relevance |
|---|---|---|
| **mtvec** | Trap vector base | Set up interrupt/exception handlers |
| **mie/mip** | Interrupt enable/pending | Route peripheral IRQs |
| **mstatus** | Status (MIE, MPIE, MPP) | Nested interrupt control |
| **mcause** | Trap cause code | Exception dispatch |
| **mtval** | Trap value | Fault address for page faults |

---

## Original Stub Description

RISC-V ISA: base integer (RV32I/RV64I), standard extensions (M/A/F/D/C/B/V), instruction formats, control/status registers (CSRs), machine mode trap handling, mie/mip/mtvec, interrupt delegation

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
