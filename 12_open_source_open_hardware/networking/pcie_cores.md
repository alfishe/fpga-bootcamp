[← 12 Open Source Open Hardware Home](../README.md) · [← Networking Home](README.md) · [← Project Home](../../../README.md)

# Open PCIe Cores

Open-source PCI Express endpoint/DMA cores — dominated by Alex Forencich's verilog-pcie and its derivatives.

---

## Core Comparison

| Core | PCIe Gen | Lanes | Interface | FPGA Support | DMA | Repository |
|---|---|---|---|---|---|---|
| **verilog-pcie** | Gen2, Gen3 | x1, x4, x8, x16 | AXI-Stream + AXI-Lite | Xilinx Ultrascale+, Versal | ✅ Multi-channel scatter-gather DMA | alexforencich/verilog-pcie |
| **Antmicro NVMe fork** | Gen3 | x4 | AXI-Stream | Xilinx Ultrascale+ | ✅ NVMe-optimized DMA | antmicro/verilog-pcie |
| **LitePCIe** | Gen2 | x1, x4 | LiteX native | Xilinx 7-series, ECP5 (experimental) | Basic | enjoy-digital/litepcie |
| **RIFFA** | Gen1, Gen2 | x1–x8 | FIFO-like | Xilinx 7-series, Intel (older) | ✅ Scatter-gather | KastnerRG/riffa |
| **OpenPCIe** | Gen1 | x1 | Research | Artix-7 (experimental) | No | Research-only |

## Selection Guide

| Scenario | Recommended | Why |
|---|---|---|
| I need production PCIe Gen3 on Xilinx | **verilog-pcie** | Best open-source PCIe solution, extensive test suite |
| I need NVMe SSD access from FPGA | **Antmicro fork** | NVMe-optimized, data-center proven |
| I want PCIe in a LiteX SoC | **LitePCIe** | LiteX-integrated, though Xilinx-limited |
| I need cross-vendor PCIe (Xilinx + Intel) | **RIFFA** | Older but multi-vendor, simpler FIFO API |

## Reality Check

- **FPGA hard PCIe blocks are proprietary**: All open PCIe cores still use the vendor's hard PCIe PHY (Xilinx PCIe hard block). The "open" part is the transaction layer + DMA engine.
- **License constraints**: verilog-pcie uses a restrictive license — check before commercial use.
- **Intel/Altera open PCIe is scarce**: Most open PCIe work targets Xilinx because of toolchain limitations.

---

## Original Stub Description

**Alex Forencich's verilog-pcie** (DMA engine, AXI bridges, Xilinx Ultrascale+/Versal), Antmicro NVMe fork, **LitePCIe**, OpenPCIe (research) — supported FPGAs and Gen support

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
