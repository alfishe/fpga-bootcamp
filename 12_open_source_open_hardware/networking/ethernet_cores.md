[← 12 Open Source Open Hardware Home](../README.md) · [← Networking Home](README.md) · [← Project Home](../../../README.md)

# Open Ethernet Cores

FPGA Ethernet MAC/PCS/PMA cores — from 1G to 100G, covering the dominant open-source ecosystem built around Alex Forencich's verilog-ethernet.

---

## Major Projects

| Project | Speeds | Interface | FPGA Support | Key Trait |
|---|---|---|---|---|
| **verilog-ethernet** | 1G, 2.5G, 10G, 25G | AXI-Stream | Xilinx 7-series, Ultrascale+, Intel Arria/Cyclone/Stratix | Modular: MAC + PCS + PMA components, mix-and-match |
| **Corundum** | 10G, 25G, 100G | AXI-Stream + PCIe DMA | Xilinx Ultrascale+, Versal | Full open-source NIC (network interface card) |
| **LiteEth** | 10/100M, 1G | LiteX native | iCE40, ECP5, Artix-7, Cyclone V | Lightweight, part of LiteX ecosystem |
| **NetFPGA** | 1G, 10G | AXI-Stream + Linux driver | NetFPGA-SUME (Virtex-7), NetFPGA-1G-CML (Kintex-7) | Academic, full network research platform |

## Selection Guide

| Need | Use | Why |
|---|---|---|
| I need a basic 1G MAC | **verilog-ethernet** 1G module | Battle-tested, AXI streaming, works everywhere |
| I'm building a custom network card | **Corundum** | Complete NIC reference: MAC + PCIe DMA + Linux driver |
| I want Ethernet in a LiteX SoC | **LiteEth** | Tight integration, automatic MAC address, UDP/IP stack included |
| I'm doing network research | **NetFPGA** | Reference pipelines, research community, Linux driver ecosystem |

## Key Designer: Alex Forencich

Most open FPGA networking traces back to **github.com/alexforencich** — his verilog-ethernet, verilog-pcie, and verilog-axis libraries form the foundation of modern open FPGA networking.

---

## Original Stub Description

**Alex Forencich's verilog-ethernet** (1G/10G/25G components, AXI stream), **Corundum** (100G open-source NIC), **LiteEth** (part of LiteX), NetFPGA ecosystem

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
