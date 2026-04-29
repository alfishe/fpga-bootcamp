[← 12 Open Source Open Hardware Home](../README.md) · [← Open Boards Home](README.md) · [← Project Home](../../../README.md)

# High-End Open Boards

FPGA boards targeting compute-heavy, PCIe-connected, or SoC-class applications — Xilinx Alveo, ZCU/Zynq, KRIA SOM, and community adaptations.

---

## Board Catalog

| Board | FPGA | Key Specs | Open-Source Targeting | Price Range |
|---|---|---|---|---|
| **Alveo U50/U200/U250** | Virtex Ultrascale+ | HBM, 100G Eth, PCIe Gen3 x16 | RTL-level targeting via Vitis/Vivado | $2,000–$8,000 |
| **Alveo U280** | Virtex Ultrascale+ | 8 GB HBM2, 32 GB DDR4, PCIe Gen3 x16 | Primary target for open FPGA compute | ~$3,500 |
| **ZCU104** | Zynq Ultrascale+ XCZU7EV | Quad A53 + R5, Mali GPU, 2 GB DDR4 | Open designs, Yocto/PetaLinux | ~$1,700 |
| **ZCU102** | Zynq Ultrascale+ XCZU9EG | Quad A53 + R5, 4 GB DDR4 | Reference for many open Zynq projects | ~$3,200 |
| **KRIA KV260** | Zynq Ultrascale+ XCK26 | SOM form-factor, cost-optimized | Xilinx App Store + open community | ~$250 |
| **KRIA KR260** | Zynq Ultrascale+ XCK26 | Robotics-focused, industrial IO | ROS 2 + FPGA acceleration | ~$350 |
| **Genesys 2** | Kintex-7 XC7K325T | 1 GB DDR3, FMC, PCIe x1 | Academic, Linux-capable open designs | ~$1,000 |

## When to Choose High-End

| Need | Board |
|---|---|
| I need HBM for bandwidth | **Alveo U280** (8 GB HBM2, 460 GB/s) |
| I need ARM cores + FPGA development | **ZCU104** or **KRIA KV260** |
| I'm doing FPGA compute research | **Alveo U250** (most documented) |
| I need FMC mezzanine expansion | **Genesys 2** or **ZCU102** |
| Budget-conscious Zynq UltraScale+ | **KRIA KV260** ($250, best price/performance) |

---

## Original Stub Description

Alveo open-source targeting, ZCU/Zynq open designs, KRIA SOM community projects — when you need PCIe or ARM cores

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
