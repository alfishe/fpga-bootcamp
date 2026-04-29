[← 11 Soft Cores And Soc Design Home](../README.md) · [← Riscv Cores Home](README.md) · [← Project Home](../../../README.md)

# High-Performance RISC-V Cores

Linux-capable, multi-issue, out-of-order RISC-V cores for large FPGAs — from Berkeley's Rocket/BOOM to OpenHW's CVA6.

---

## Core Comparison

| Core | ISA | Pipeline | LUTs | fmax (FPGA) | Linux | Generator |
|---|---|---|---|---|---|---|
| **Rocket** | RV64IMAFDC | 5-stage, single-issue | ~15,000+ | 100+ MHz | ✅ | Chisel |
| **BOOM** | RV64IMAFDC | Out-of-order, 2–4 wide | ~30,000+ | 50+ MHz | ✅ | Chisel |
| **CVA6 (Ariane)** | RV64IMAFDC | 6-stage, single-issue | ~25,000+ | 50+ MHz | ✅ | SystemVerilog |
| **XiangShan** | RV64IMAFDC | Out-of-order, 6-wide | ~100,000+ | — (ASIC-targeted) | ✅ | Chisel |

## Why These Matter for FPGA

| Core | FPGA Use Case |
|---|---|
| **Rocket** | Most practical Linux-on-FPGA option. Used in Chipyard (Berkeley SoC framework). Runs on Kintex-7/Zynq-sized devices. |
| **BOOM** | Research platform for OoO architecture. Needs large FPGA (Kintex-7 325T+). Impractical for production FPGA use. |
| **CVA6** | SystemVerilog (no Chisel dependency), OpenHW-maintained. Best for teams wanting readable RTL. |
| **XiangShan** | ASIC research. FPGA prototypes exist on multi-FPGA systems (VCU118 ×4). Not practical for single-FPGA. |

## FPGA Reality Check

All four cores were **designed for ASIC**, not FPGA:
- ASIC fmax targets: 1–2 GHz → FPGA achieves 50–100 MHz
- LUT counts (15K–100K+) consume entire mid-to-large FPGAs
- Memory subsystems (L1/L2 caches) are large and complex

For practical Linux on FPGA, **VexRiscv (Linux variant)** or a **hard ARM core (Zynq/Cyclone V SoC)** are better choices. These high-perf cores are for architecture research and ASIC prototyping.

---

## Original Stub Description

High-perf survey: BOOM (Berkeley OoO, RV64GC), Rocket (in-order, Chisel generator), CVA6 (ex-Ariane, RV64GC), XiangShan — comparison: pipeline depth, branch prediction, multi-issue, Linux-ready

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
