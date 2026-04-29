[← 11 Soft Cores And Soc Design Home](../README.md) · [← Riscv Cores Home](README.md) · [← Project Home](../../../README.md)

# Ibex / CV32E40P — Security-Hardened RISC-V

Ibex is a production-quality RV32IMCB core originally developed at ETH Zürich, now maintained by lowRISC as part of OpenTitan — where it serves as the Root of Trust processor. It's the most security-audited open soft core.

---

## Architecture

| Parameter | Value |
|---|---|
| **ISA** | RV32IMCB (Zicsr, Zifencei, Zicntr) |
| **Pipeline** | 2-stage (fetch → execute) or 3-stage (with optional prefetch buffer) |
| **LUTs** | ~3,000–6,000 (config-dependent) |
| **fmax** | 150+ MHz on Artix-7, Kintex-7 |
| **Debug** | JTAG (RISC-V debug spec 0.13), hardware breakpoints |
| **Security** | PMP (Physical Memory Protection), secure boot hooks |

## Variants

| Variant | Pipeline | Features | Target |
|---|---|---|---|
| **Ibex (original)** | 2-stage | RV32IMC | General embedded |
| **CV32E40P (RI5CY)** | 4-stage | RV32IMFC + custom DSP extensions | Higher performance, PULP |
| **CV32E40S** | 2-stage | RV32IM + safety/security features (PMP, ECC) | OpenTitan RoT, safety-critical |

## Why Ibex Matters

1. **Security verification**: Undergoing formal verification as part of OpenTitan — unusual for an open core
2. **Production silicon**: Taped out in multiple ASICs including Google's Titan chip
3. **OpenHW Group**: CORE-V family maintains multiple verified configurations
4. **FPGA-friendly**: Primary development on FPGA before ASIC tape-out

---

## Original Stub Description

Ibex / CV32E40P: OpenTitan's core, 2–3 stage, RV32IMCB, security features, OpenHW Group, formal verification status

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
