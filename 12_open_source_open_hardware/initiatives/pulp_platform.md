[← 12 Open Source Open Hardware Home](../README.md) · [← Initiatives Home](README.md) · [← Project Home](../../../README.md)

# PULP Platform — Parallel Ultra-Low-Power Computing

ETH Zürich's PULP (Parallel Ultra-Low-Power) platform is one of the most impactful academic open-source silicon projects — 50+ ASIC tape-outs, multiple RISC-V cores adopted by industry, and fully FPGA-compatible.

---

## Core Projects

| Project | Description | FPGA Status |
|---|---|---|
| **PULPissimo** | Single-core microcontroller SoC (CV32E40P) | ✅ Full FPGA support (Xilinx, Intel) |
| **PULP** | Multi-core cluster platform | ✅ FPGA proven |
| **Snitch** | Minimal RISC-V core with custom accelerators | ✅ FPGA support |
| **Ara** | RISC-V vector processor (RVV 1.0) | ✅ FPGA (large devices) |
| **Mempool** | 256-core shared-L1 manycore | 🟡 Research, large FPGA needed |
| **Occamy** | Chiplet-based HPC system | 🟡 Advanced research |

## RISC-V Cores from PULP

| Core | Type | Adopted By |
|---|---|---|
| **CV32E40P (RI5CY)** | RV32IMFCXpulp, 4-stage in-order | OpenHW Group, GreenWaves GAP8 |
| **CVE2 (Zero-riscy)** | RV32IMC, 2-stage, ultra-low area | OpenHW Group |
| **CV32E40S** | RV32IM[F]Zfinx, safety features | OpenHW Group (safety certified) |
| **Snitch** | RV32IMA, minimal + custom ISA | ETH research, HPC prototyping |
| **Ara** | RVV 1.0 vector unit (attached to CVA6) | HPC, ML acceleration research |

## Why PULP Matters for FPGA Developers

1. **Production-quality RISC-V cores**: CV32E40P/CVE2 are OpenHW-verified, not just research toys
2. **Full SoC templates**: PULPissimo gives you a working SoC with RISC-V + peripherals + debug in hours
3. **FPGA-first**: PULP uses FPGA as the primary prototyping platform
4. **Hardware/software co-design**: PULP SDK provides GCC + OpenMP + FreeRTOS targeting their cores
5. **Energy-proportional computing**: Many research ideas on dynamic voltage/frequency scaling originate here

---

## Original Stub Description

**PULP Platform** (ETH Zürich) — parallel ultra-low-power computing, multiple ASIC tape-outs, RISC-V cores (CV32E40P, Snitch, Ara vector), FPGA-friendly

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
