[← 06 IP & Cores Home](../README.md) · [External Interfaces](README.md)

# Chip-to-Chip Interfaces — PCIe, CXL, CCIX, UCIe

The highest-bandwidth interfaces in modern FPGAs. These protocols connect the FPGA to CPUs, GPUs, other FPGAs, and chiplets at speeds from 2.5 GT/s (PCIe Gen1) up to 256 GT/s (UCIe). All require hardened SerDes transceivers — soft implementations are not practical.

---

## Overview

| Interface | Speed per Lane | Lanes | Total BW | Encoding | FPGA Support |
|---|---|---|---|---|---|
| **PCIe Gen1** | 2.5 GT/s | ×1–×16 | 4 GB/s | 8b/10b | 7-series, ECP5, PolarFire |
| **PCIe Gen2** | 5.0 GT/s | ×1–×8 | 8 GB/s | 8b/10b | 7-series, PolarFire |
| **PCIe Gen3** | 8.0 GT/s | ×1–×16 | ~16 GB/s | 128b/130b | UltraScale, Arria 10, Stratix 10 |
| **PCIe Gen4** | 16.0 GT/s | ×1–×16 | ~32 GB/s | 128b/130b | UltraScale+, Agilex |
| **PCIe Gen5** | 32.0 GT/s | ×1–×16 | ~64 GB/s | 128b/130b FLIT | Versal, Agilex 7 |
| **PCIe Gen6** | 64.0 GT/s | ×1–×16 | ~128 GB/s | PAM4 FLIT | Future (2025+) |
| **CXL 1.1/2.0** | 32 GT/s (Gen5) | ×8/×16 | ~64 GB/s | 128b/130b FLIT | Versal, Agilex 7 |
| **CXL 3.0** | 64 GT/s (Gen6) | ×16 | ~128 GB/s | PAM4 FLIT | Future |
| **CCIX** | 25 GT/s | ×16 | ~50 GB/s | 128b/130b | Discontinued (replaced by CXL) |
| **UCIe** | 2–16 GT/s | Up to 256 lanes | ~2 TB/s | Custom | Future chiplets |
| **Interlaken** | 10–28 Gbps | Up to 48 lanes | ~1.3 Tbps | 64b/67b | Stratix 10, UltraScale+ |
| **Aurora** | 0.5–28 Gbps | ×1–×16 | N/A | 8b/10b or 64b/66b | Xilinx only (proprietary) |

---

## PCIe — The Universal Backbone

PCI Express is the de facto standard for FPGA-host communication. See the [PCIe deep dives](../pcie/) for:
- [Hard block comparison](../pcie/pcie_hard_blocks.md) — Gen1–Gen5 across all vendors
- [Configuration](../pcie/pcie_configuration.md) — BARs, MSI/MSI-X, AER
- [DMA engines](../pcie/pcie_dma.md) — XDMA, QDMA, scatter-gather

**Key FPGA family support:**

| FPGA Family | Max Gen | Max Width | CXL Support | Notes |
|---|---|---|---|---|
| Xilinx Artix-7 | Gen2 | ×4 | No | Budget PCIe for data acquisition |
| Xilinx Kintex-7 | Gen2 | ×8 | No | Mid-range accelerators |
| Xilinx Kintex UltraScale+ | Gen4 | ×8 | No | AI/ML inference cards |
| Xilinx Versal | Gen5 | ×16 | CXL 1.1/2.0 | CPM5 block with NoC integration |
| Intel Arria 10 | Gen3 | ×8 | No | Avalon-MM interface |
| Intel Stratix 10 DX | Gen3 | ×16 | No | DCI-attached memory focus |
| Intel Agilex 7 | Gen5 | ×16 | CXL 1.1 | P-Tile hard block |
| Microchip PolarFire | Gen2 | ×4 | No | Low-power edge applications |

---

## CXL — Compute Express Link

CXL is PCIe Gen5/Gen6 with three new protocols layered on top:
- **CXL.io** — PCIe-compatible I/O (legacy compatibility)
- **CXL.cache** — Coherent cache access between CPU and FPGA accelerator
- **CXL.mem** — Direct memory access to CPU-attached DDR (FPGA uses host memory as its own)

### Why CXL Matters for FPGAs

Traditional PCIe DMA copies data between host and FPGA memory. CXL.mem allows the FPGA to **directly access host memory with cache coherency** — no DMA copies, no driver bounce buffers.

```
Traditional PCIe:
  Host DDR ──→ DMA copy ──→ FPGA DDR ──→ FPGA computes ──→ DMA copy ──→ Host DDR

CXL.mem:
  Host DDR ←──────→ FPGA computes (direct cache-coherent access)
```

### FPGA CXL Support

| FPGA | CXL Version | Max Speed | CXL.cache | CXL.mem | Availability |
|---|---|---|---|---|---|
| AMD Versal Premium | CXL 2.0 | Gen5 ×16 | Yes | Yes | Production |
| Intel Agilex 7 | CXL 1.1 | Gen5 ×16 | Yes | Yes | Production |
| Intel Agilex 5 | CXL 2.0 | Gen5 ×8 | Yes | Yes | Sampling |
| AMD Versal 2 | CXL 3.0 | Gen6 ×16 | Yes | Yes | Roadmap |

---

## CCIX — Cache Coherent Interconnect for Accelerators

CCIX was an early competitor to CXL, led by ARM, Qualcomm, and Xilinx. It is now effectively **discontinued** — the industry consolidated on CXL. Mentioned here only for historical context when reading pre-2022 accelerator documentation.

| Aspect | CCIX | CXL |
|---|---|---|
| Base PHY | PCIe Gen4/Gen5 | PCIe Gen5/Gen6 |
| Cache coherency | Yes | Yes |
| Memory pooling | Yes | Yes (CXL.mem) |
| Industry adoption | Xilinx, ARM, Ampere | Intel, AMD, NVIDIA, Broadcom, Samsung |
| Status | Discontinued (2022) | Active, dominant standard |

---

## UCIe — Universal Chiplet Interconnect Express

UCIe is the emerging standard for **die-to-die interconnect** in chiplet-based designs. It is not a board-level protocol like PCIe — it connects dies inside a single package (2.5D/3D stacking).

### UCIe Parameters

| Parameter | Value |
|---|---|
| Data rate | 2–16 GT/s per lane (up to 32 GT/s in roadmap) |
| Lane width | Standard: 16 data + 1 valid; Advanced: 64 data + 4 valid |
| Max lanes | 256 (standard) / 1024 (advanced) |
| Bump pitch | 45–130 µm (standard) / 25–55 µm (advanced) |
| Reach | <2 mm (standard) / <10 mm (advanced, bridge die) |

### FPGA Relevance

UCIe is currently **not available in commercial FPGAs** (as of 2025). However:
- AMD's Versal 2 and Intel's next-gen FPGAs are expected to support UCIe for HBM and companion die attachment
- Custom ASICs using FPGA IP may use UCIe to connect to HBM3 or other chiplets
- Open-source UCIe controllers are in development (CHIPS Alliance)

---

## Interlaken — High-Speed Chip-to-Chip

Interlaken is a high-bandwidth serial protocol developed by Cisco and Cortina, popular in networking:
- 10–28 Gbps per lane, up to 48 lanes
- 64b/67b encoding with strong error detection
- Flow control and lane striping built-in
- Common in 100G/400G Ethernet MAC-to-PHY interfaces

### FPGA Support

| FPGA Family | Interlaken Support | Max Rate |
|---|---|---|
| Intel Stratix 10 | Hard IP | 28 Gbps × 12 lanes |
| Intel Agilex 7 | Hard IP | 28 Gbps × 24 lanes |
| Xilinx UltraScale+ | Soft core only | 25 Gbps × 12 lanes |
| Xilinx Versal | Soft core only | 32 Gbps × 16 lanes |

---

## Aurora — Xilinx Proprietary

Aurora is a **lightweight, Xilinx-only** serial protocol for FPGA-to-FPGA or FPGA-to-ASIC links:
- Very low overhead (just 8b/10b or 64b/66b framing)
- No flow control by default (user must implement)
- Scales from 0.5 Gbps to 28 Gbps
- Free IP from Xilinx (no license required)

**Use when:** You control both ends of the link and both are Xilinx FPGAs. Avoid when interfacing to third-party devices.

---

## Speed Comparison Summary

```
Relative bandwidth (log scale, approximate)
│
├─ 1 Tbps  ─── UCIe (256 lanes @ 16 GT/s)
├─ 100 Gbps ─── PCIe Gen6 ×16, Interlaken ×12
├─  10 Gbps ─── PCIe Gen5 ×4, CXL ×8, Aurora ×4
├─   1 Gbps ─── PCIe Gen3 ×1, SATA 6G
├─ 100 Mbps ─── USB 2.0 HS, CAN-FD
└─  10 Mbps ─── SPI @ 10 MHz, UART
```

---

## Selecting an Interface

| Scenario | Recommended Interface | Why |
|---|---|---|
| FPGA accelerator in a server | PCIe Gen4/Gen5 ×16 | Standard, every server supports it |
| FPGA sharing CPU memory directly | CXL 1.1/2.0 | Cache-coherent, no DMA copies |
| FPGA-to-FPGA on same board (Xilinx only) | Aurora | Free, minimal overhead, easy |
| FPGA-to-FPGA on same board (multi-vendor) | PCIe | Standard, works across vendors |
| 100G/400G networking datapath | Interlaken | Designed for MAC-to-PHY |
| Future chiplet-based FPGA | UCIe | Die-to-die, package-level |

---

## FPGA Family Selection for High-Speed Interconnect

| Application | Minimum FPGA Family | Transceiver Requirement |
|---|---|---|
| PCIe Gen3 ×4 | Artix-7 / Cyclone V GX | GTX / GX transceivers |
| PCIe Gen4 ×8 | Kintex UltraScale+ / Arria 10 | GTY / GX transceivers |
| PCIe Gen5 ×16 | Versal / Agilex 7 | GTM / P-Tile |
| CXL 1.1 | Versal Premium / Agilex 7 | Gen5 + CXL logic |
| 100G networking | Stratix 10 / Virtex UltraScale+ | 25G+ transceivers |
| 400G networking | Versal / Agilex 7 | 56G+ transceivers |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| PCI Express Base Specification 6.0 | PCI-SIG | Full PCIe protocol, electrical, mechanical |
| CXL 2.0 Specification | CXL Consortium | CXL.io, .cache, .mem protocols |
| UCIe 1.0 Specification | UCIe Consortium | Die-to-die interconnect for chiplets |
| Interlaken Protocol Definition v1.2 | Cortina/Cisco | Interlaken framing, flow control, lane management |
| Xilinx PG074 — Aurora 8B/10B | AMD/Xilinx | Xilinx proprietary lightweight serial protocol |
| [PCIe Hard Blocks](../pcie/pcie_hard_blocks.md) | This KB | Detailed vendor PCIe block comparison |
| [Transceivers](../transceivers/README.md) | This KB | SerDes PHY deep dive |
