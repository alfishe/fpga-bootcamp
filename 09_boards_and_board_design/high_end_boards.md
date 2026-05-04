[← Board Design](README.md) · [← Project Home](../README.md)

# High-End Development Boards — Alveo, Zynq, KRIA & Intel Agilex

FPGA boards targeting compute-heavy, PCIe-connected, or SoC-class applications — AMD/Xilinx Alveo data-center cards, ZCU/Zynq development kits, KRIA system-on-modules, and Intel Agilex/Stratix 10 platforms. These are not hobbyist boards: they have HBM, multi-gigabit transceivers, hardened ARM processors, and price tags from $250 to $8,000.

---

## Overview

High-end FPGA boards serve four distinct communities: **data-center acceleration** (Alveo with HBM and PCIe Gen3/4 x16, Agilex 7 with PCIe Gen5/CXL), **embedded SoC development** (Zynq UltraScale+ and Stratix 10 SX with ARM Cortex-A53 + FPGA fabric, Agilex 5 with A76/A55), **high-speed networking** (Agilex 7 I-Series with R-Tile PCIe 5.0 and E-Tile 112G transceivers), and **rapid prototyping** (KRIA SOMs that bring Zynq capability to a $250 price point). Open-source projects target all four — from FINN ML inference on Alveo to OPAE on Agilex to LiteX on Zynq to PYNQ on KRIA.

---

## Board Catalog

| Board | FPGA | Key Specs | Open-Source Targeting | Price Range |
|---|---|---|---|---|
| **Alveo U50** | Virtex UltraScale+ XCU50 | 8 GB HBM2, 100G Eth, PCIe Gen3 x16 | RTL-level targeting via Vitis/Vivado | $4,000–$6,000 |
| **Alveo U200** | Virtex UltraScale+ XCU200 | 32 GB DDR4, PCIe Gen3 x16 | XRT runtime, OpenCL kernels | $5,000–$7,000 |
| **Alveo U250** | Virtex UltraScale+ XCU250 | 64 GB DDR4, PCIe Gen3 x16 | Most documented for open compute | $6,000–$8,000 |
| **Alveo U280** | Virtex UltraScale+ XCU280 | 8 GB HBM2 + 32 GB DDR4, PCIe Gen3 x16 | Primary target for open FPGA compute research | ~$3,500 |
| **ZCU104** | Zynq UltraScale+ XCZU7EV | Quad A53 + R5, Mali GPU, 2 GB DDR4 | Yocto/PetaLinux, LiteX, PYNQ | ~$1,700 |
| **ZCU102** | Zynq UltraScale+ XCZU9EG | Quad A53 + R5, 4 GB DDR4 | Reference for many open Zynq projects | ~$3,200 |
| **ZCU106** | Zynq UltraScale+ XCZU7EV | Quad A53 + R5, Mali, 2 GB DDR4, DP TX | Video/display focused | ~$2,000 |
| **KRIA KV260** | Zynq UltraScale+ XCK26 | SOM form-factor, cost-optimized | Xilinx App Store + open community | ~$250 |
| **KRIA KR260** | Zynq UltraScale+ XCK26 | Robotics-focused, industrial I/O | ROS 2 + FPGA acceleration | ~$350 |
| **Genesys 2** | Kintex-7 XC7K325T | 1 GB DDR3, FMC, PCIe x1 | Academic, Linux-capable open designs | ~$1,000 |
| **VCU118** | Virtex UltraScale+ XCVU9P | 4 GB DDR4, 2× FMC HPC, 100G Eth | Advanced research, Ventus GPU target | ~$5,000 |
| **Agilex 7 F-Series DK** | Intel Agilex 7 AGFB014 | P-Tile + E-Tile (112G), 4 GB DDR4, PCIe Gen4 x16 | OPAE runtime, PCIe 4.0 / 112G networking | ~$3,500 |
| **Agilex 7 I-Series DK** | Intel Agilex 7 AGIB027 | 2× R-Tile + F-Tile, 64 GB DDR4 ECC, PCIe Gen5/CXL | OPAE runtime, PCIe 5.0 / CXL acceleration | ~$4,000 |
| **Stratix 10 GX DK** | Intel Stratix 10 GX 1SG280 | H-Tile (28.3G), 2 GB DDR4, PCIe Gen3 x8 | Transceiver prototyping, Quartus Prime Pro | ~$3,000 |
| **Stratix 10 SX SoC DK** | Intel Stratix 10 SX 1SX280 | Quad A53 + FPGA, 16+4 GB DDR4, PCIe Gen3 x16 | SoC Linux (Yocto), ARM DS, HPS development | ~$5,000 |
| **Agilex 5 E-Series DK** | Intel Agilex 5 A5ED065 | Dual A76 + A55, 8+8 GB DDR4 + 4 GB LPDDR4 | Next-gen Intel SoC, edge AI, MIPI | ~$3,000 |

---

## Alveo — Data-Center FPGA Acceleration

### Architecture

```mermaid
flowchart TD
    subgraph HOST["Host Server (x86)"]
        CPU["CPU<br/>(Xeon/EPYC)"]
        DRIVER["XRT Driver<br/>(Open-source)"]
    end

    subgraph ALVEO["Alveo Card"]
        FPGA_CORE["FPGA Fabric<br/>(Virtex UltraScale+)"]
        HBM["HBM2 Stack<br/>(8 GB, 460 GB/s)"]
        DDR["DDR4<br/>(32 GB, 25 GB/s)"]
        PCIE["PCIe Gen3 x16<br/>(~16 GB/s)"]
        ETH["100G Ethernet<br/>(CMAC)"]
    end

    CPU <-->|"PCIe Gen3 x16"| PCIE
    PCIE <--> FPGA_CORE
    FPGA_CORE <-->|"460 GB/s"| HBM
    FPGA_CORE <-->|"25 GB/s"| DDR
    FPGA_CORE <--> ETH
```

### Key Specifications

| Model | LUTs | BRAM (Mb) | DSP | HBM2 | DDR4 | PCIe | Price |
|---|---|---|---|---|---|---|---|
| **U50** | 872K | 1,344 | 5,952 | 8 GB | None | Gen3 x16 | ~$4,000 |
| **U200** | 1,272K | 1,704 | 9,072 | None | 64 GB | Gen3 x16 | ~$6,000 |
| **U250** | 1,728K | 2,160 | 12,288 | None | 64 GB | Gen3 x16 | ~$7,000 |
| **U280** | 1,304K | 2,016 | 9,072 | 8 GB | 32 GB | Gen3 x16 | ~$3,500 |

### Open-Source Stack for Alveo

| Component | Tool | License |
|---|---|---|
| **Runtime** | XRT (Xilinx RunTime) | Apache 2.0 |
| **Kernel development** | Vitis HLS (C/C++ → RTL) | Proprietary (free WebPACK for some devices) |
| **RTL development** | Vivado | Proprietary |
| **Networking** | Open NIC (Intel + Xilinx) | BSD |
| **Shell** | Xilinx Shell (2RP) | Binary, documented |

---

## Zynq UltraScale+ — ARM + FPGA SoC

The Zynq UltraScale+ combines a quad-core ARM Cortex-A53 (64-bit Linux-capable) with FPGA fabric on a single chip. The PS (Processing System) and PL (Programmable Logic) communicate via AXI interfaces at up to 128 Gbps.

### Zynq Architecture

```mermaid
flowchart LR
    subgraph PS["Processing System (PS)"]
        A53["Quad Cortex-A53<br/>(64-bit, Linux)"]
        R5["Dual Cortex-R5<br/>(Real-time)"]
        GPU["Mali-400 MP2<br/>(ZU7EV only)"]
        DDR_PS["DDR4 Controller<br/>(4 GB)"]
        PERIPH["Peripherals<br/>(USB, Eth, SD, UART, SPI, I2C)"]
    end

    subgraph PL["Programmable Logic (PL)"]
        FABRIC["FPGA Fabric<br/>(LUTs, BRAM, DSP)"]
        HP["AXI HP Ports<br/>(4× 128-bit, PS←PL DMA)"]
        HPC["AXI HPC Ports<br/">(2× 128-bit, coherent)"]
        GP["AXI GP Ports<br/>(4× 32-bit, register access)"]
    end

    A53 <-->|"AXI coherent<br/>(ACP/HPC)"| HPC
    A53 <-->|"AXI HP<br/>(DMA)"| HP
    PERIPH <-->|"AXI GP<br/">(register)"| GP
    DDR_PS <-->|"AXI HP<br/">(PL→DDR)"| HP
    GPU --> DDR_PS
```

### Zynq Board Comparison

| Feature | ZCU102 | ZCU104 | KV260 | KR260 |
|---|---|---|---|---|
| **FPGA** | XCZU9EG | XCZU7EV | XCK26 | XCK26 |
| **LUTs** | 600K | 230K | 154K | 154K |
| **ARM A53** | 4 | 4 | 4 | 4 |
| **ARM R5** | 2 | 2 | 2 | 2 |
| **Mali GPU** | No | Yes | Yes | Yes |
| **DDR4** | 4 GB | 2 GB | 4 GB | 4 GB |
| **FMC** | 2× HPC | 1× HPC | None (carrier) | None (carrier) |
| **Form factor** | Dev board | Dev board | SOM + carrier | SOM + carrier |
| **Price** | ~$3,200 | ~$1,700 | ~$250 | ~$350 |
| **Best for** | Reference design, FMC | Video, AI/ML | Edge AI, cost-optimized | Robotics |

---

## KRIA — Zynq at Hobbyist Prices

KRIA SOMs bring Zynq UltraScale+ to a $250 price point — previously impossible for ARM + FPGA SoC development.

### KV260 Vision AI Starter Kit

| Component | Detail |
|---|---|
| **SOM** | KRIA K26 (XCK26, 154K LUTs, quad A53, Mali) |
| **Carrier** | Starter carrier with camera connector, DP, USB, Ethernet, SD |
| **Out-of-box apps** | Smartcam, AI inference (pre-built) |
| **Software** | Ubuntu 22.04 LTS, PYNQ, Vitis-AI |
| **Open-source targeting** | PYNQ framework, VART runtime, custom PL via Vivado |

### KR260 Robotics Starter Kit

Same SOM as KV260 but with a robotics-focused carrier: CAN bus, RS-485, additional GPIO, and ROS 2 integration.

---

## Intel Agilex & Stratix 10 — The Alternative Ecosystem

Intel's (now Altera's) high-end FPGA lineup spans three generations: Stratix 10 (14 nm, ARM Cortex-A53 SoC variant), Agilex 7 (10 nm SuperFin, PCIe 4.0/5.0 + 112G transceivers), and Agilex 5 (mid-range, ARM Cortex-A76/A55 SoC with LPDDR4). While AMD/Xilinx dominates the open-source FPGA community, Intel boards are essential for designs requiring Intel-specific hard IP (EMIF, HPS, E-Tile 112G transceivers) or CXL/PCIe 5.0 connectivity.

### Intel FPGA Architecture

```mermaid
flowchart TD
    subgraph HOST["Host Server (x86)"]
        CPU["CPU"]
        DRIVER["OPAE Driver<br/>(Open-source)"]
    end

    subgraph AGILEX["Agilex 7 Card"]
        FPGA_CORE["FPGA Fabric<br/>(Agilex 7 I-Series / F-Series)"]
        TILE_R["R-Tile<br/>(PCIe 5.0 / CXL)"]
        TILE_F["F-Tile<br/>(56G PAM4)"]
        TILE_E["E-Tile<br/>(112G PAM4)"]
        DDR4["DDR4 DIMM<br/>(4 ch, 3200 MT/s)"]
    end

    CPU <-->|"PCIe 4.0/5.0"| TILE_R
    TILE_R <--> FPGA_CORE
    FPGA_CORE <--> TILE_F
    FPGA_CORE <--> TILE_E
    FPGA_CORE <-->|"25.6 GB/s"| DDR4
```

### Key Specifications

| Model | LEs | BRAM (Mb) | DSP | Transceivers | Memory | PCIe | Price |
|---|---|---|---|---|---|---|---|
| **Agilex 7 F-Series DK** | 1,437K | 679 | 3,744 | P-Tile + E-Tile (112G) | 4 GB DDR4 (3+1 HPS) | Gen4 x16 | ~$3,500 |
| **Agilex 7 I-Series DK** | 2,700K | 1,168 | 6,720 | 2× R-Tile + F-Tile | 64 GB DDR4 ECC | Gen5 x16 / CXL | ~$4,000 |
| **Stratix 10 GX DK** | 2,753K | 1,159 | 5,760 | H-Tile (28.3G) | 2 GB DDR4 | Gen3 x8 | ~$3,000 |
| **Stratix 10 SX SoC DK** | 2,753K | 1,159 | 5,760 | H-Tile + quad A53 | 16 GB FPGA + 4 GB HPS DDR4 | Gen3 x16 | ~$5,000 |
| **Agilex 5 E-Series DK** | 345K | 161 | 912 | F-Tile (28G) | 8+8 GB DDR4 + 4 GB LPDDR4 | Gen3 x4 (FMC) | ~$3,000 |

### Intel Board Comparison

| Feature | Agilex 7 F-Series | Agilex 7 I-Series | Stratix 10 GX | Stratix 10 SX | Agilex 5 E-Series |
|---|---|---|---|---|---|
| **FPGA** | AGFB014R24 | AGIB027R29 | 1SG280HU | 1SX280HU | A5ED065BB32 |
| **LEs** | 1,437K | 2,700K | 2,753K | 2,753K | 345K |
| **ARM cores** | — | — | — | Quad A53 | Dual A76 + Dual A55 |
| **DDR4** | 4 GB | 64 GB | 2 GB | 16 GB FPGA + 4 GB HPS | 8 GB FPGA + 8 GB HPS |
| **LPDDR4** | — | — | — | — | 4 GB |
| **FMC/FMC+** | — | — | — | 2× FMC+ | FMC+ |
| **QSFP** | 2× QSFPDD | 2× QSFPDD | 2× QSFP28 | 2× QSFP28 | 2× QSFP + 2× SFP28 |
| **Form factor** | PCIe card | PCIe card | PCIe card | Tabletop | Tabletop |
| **Price** | ~$3,500 | ~$4,000 | ~$3,000 | ~$5,000 | ~$3,000 |
| **Best for** | PCIe 4.0, 112G networking | PCIe 5.0, CXL, highest bandwidth | Transceiver prototyping | ARM + FPGA SoC | Mid-range SoC, edge AI |

### Open-Source Stack for Intel FPGAs

| Component | Tool | License |
|---|---|---|
| **Runtime** | OPAE (Open Programmable Acceleration Engine) | BSD 3-Clause |
| **Kernel development** | oneAPI / HLS | Proprietary (free for Intel FPGAs) |
| **RTL development** | Quartus Prime Pro | Proprietary (1-year license with dev kit) |
| **Simulation** | ModelSim-Intel FPGA Starter | Free |
| **SoC Linux** | Yocto / Angstrom on HPS | Open-source |

> **OPAE vs XRT**: Intel's OPAE and AMD's XRT serve the same purpose — a user-space driver and API for FPGA acceleration. OPAE is BSD-licensed and works with both Agilex and Stratix 10. XRT is Apache 2.0 and works with Alveo. Both support OpenCL kernels and RTL-level acceleration, but neither is cross-vendor compatible.

> **The Quartus licensing catch**: Unlike Xilinx's free WebPACK for some devices, Intel high-end FPGAs require Quartus Prime Pro — which is only available as a paid license or a 1-year license included with a dev kit purchase. After the first year, you must pay for continued Quartus Pro access. This is a significant ongoing cost that does not apply to Xilinx boards.

---

## When to Choose High-End

| Need | Board | Why |
|---|---|---|
| I need HBM for bandwidth | **Alveo U280** | 8 GB HBM2 at 460 GB/s — no other option at this price |
| I need ARM cores + FPGA dev | **ZCU104** or **KV260** | Zynq UltraScale+ PS + PL |
| I'm doing FPGA compute research | **Alveo U250** | Most documented, largest fabric |
| I need FMC mezzanine expansion | **Genesys 2** or **ZCU102** | FMC HPC connectors for ADC/DAC cards |
| Budget Zynq UltraScale+ | **KV260** | $250 for quad A53 + 154K LUT FPGA |
| ML inference at the edge | **KV260** | Pre-built AI apps + Vitis-AI |
| Robotics with FPGA acceleration | **KR260** | CAN/RS-485 + ROS 2 + FPGA |
| I need PCIe 5.0 or CXL | **Agilex 7 I-Series DK** | Only dev kit with R-Tile PCIe 5.0 + CXL x16 |
| I need 112G transceivers | **Agilex 7 F-Series DK** | E-Tile 112G PAM4 — no Xilinx equivalent at this price |
| Intel SoC with ARM + FPGA | **Stratix 10 SX SoC DK** | Quad A53 + FPGA, 2× FMC+, QSFP28 |
| Next-gen Intel SoC | **Agilex 5 E-Series DK** | A76/A55 + LPDDR4 + MIPI — newest Intel SoC platform |

---

## Decision Guide

```mermaid
flowchart TD
    A["Need a high-end FPGA board?"] --> B{"Vendor preference?"}
    B -->|"AMD/Xilinx"| C{"ARM cores needed?"}
    B -->|"Intel/Altera"| D{"ARM cores needed?"}
    C -->|"Yes"| E{"Budget?"}
    C -->|"No"| F{"PCIe required?"}
    D -->|"Yes"| G{"Budget?"}
    D -->|"No"| H{"PCIe / CXL speed?"}
    E -->|"$250–400"| I["KRIA KV260/KR260<br/>Zynq SOM + carrier"]
    E -->|"$1,700+"| J{"Need FMC?"}
    J -->|"Yes"| K["ZCU102 ($3,200)<br/>2× FMC HPC"]
    J -->|"No"| L["ZCU104 ($1,700)<br/>Video/AI focused"]
    F -->|"Yes"| M{"Need HBM?"}
    F -->|"No"| N["Genesys 2 ($1,000)<br/>Kintex-7, academic"]
    M -->|"Yes"| O["Alveo U280<br/>8 GB HBM2, ~$3,500"]
    M -->|"No"| P["Alveo U200/U250<br/>DDR4 only, ~$6,000+"]
    G -->|"$3,000"| Q["Agilex 5 E-Series DK<br/>A76/A55 + LPDDR4"]
    G -->|"$5,000+"| R["Stratix 10 SX SoC DK<br/>Quad A53 + 2× FMC+"]
    H -->|"PCIe 5.0 / CXL"| S["Agilex 7 I-Series DK (~$4,000)<br/>R-Tile, highest bandwidth"]
    H -->|"PCIe 4.0 / 112G"| T["Agilex 7 F-Series DK (~$3,500)<br/>E-Tile 112G transceivers"]
    H -->|"PCIe 3.0 only"| U["Stratix 10 GX DK (~$3,000)<br/>Transceiver prototyping"]
```

---

## When to Use / When NOT to Use

### When to Use

- **Data-center acceleration** — Alveo for ML inference, networking, quantitative finance
- **Edge AI** — KV260 with Vitis-AI for camera-based inference
- **Zynq Linux + FPGA** — any Zynq UltraScale+ board for custom hardware + software co-design
- **FMC mezzanine I/O** — ZCU102/VCU118 for high-speed ADC/DAC/radio cards
- **PCIe 5.0 / CXL acceleration** — Agilex 7 I-Series is the only dev kit with R-Tile and CXL
- **112G networking** — Agilex 7 F-Series with E-Tile for next-gen optical networking
- **Intel SoC development** — Stratix 10 SX or Agilex 5 for ARM + FPGA on Intel platform

### When NOT to Use

- **Hobbyist projects** — these boards are expensive and require proprietary tools (Vivado, Quartus)
- **Learning FPGA basics** — a $15 Tang Nano or $70 iCEBreaker is a better starting point
- **Pure software development** — if you don't need the FPGA fabric, use a plain ARM SBC
- **Cross-vendor development** — neither OPAE nor XRT is cross-vendor; pick one ecosystem and commit
- **Budget Intel SoC** — Agilex 5 E-Series at $3,000 is 10× the cost of a KRIA KV260 ($250) for a comparable SoC experience

---

## Best Practices

1. **Start with KRIA for Zynq development** — the $250 KV260 gives you the same Zynq experience as a $3,200 ZCU102 for most use cases
2. **Use XRT for Alveo development** — the open-source XRT runtime provides a consistent API across all Alveo cards
3. **Use OPAE for Intel FPGA development** — the BSD-licensed OPAE SDK provides the same abstraction for Agilex/Stratix 10
4. **Use PYNQ for Zynq prototyping** — Jupyter + Python + FPGA accelerators; fastest path from idea to running code
5. **Don't buy ZCU102 unless you need FMC** — the ZCU104 is $1,500 cheaper and has the same PS
6. **Budget for Quartus Pro license renewal** — Intel dev kits include a 1-year Quartus Pro license; plan for the ongoing cost if you're not using open-source tools exclusively

---

## Antipatterns

- **The Alveo for Hobby Projects** — buying a $5,000 Alveo card for a personal project; the power, cooling, and host requirements make it impractical
- **The ZCU102 Without FMC** — spending $3,200 on a ZCU102 and never using the FMC connectors; a ZCU104 or KV260 would have been sufficient
- **The Custom Zynq Board** — designing a custom Zynq carrier board without first prototyping on a KRIA SOM; the SOM approach is faster and cheaper
- **The Stratix 10 SX as a Zynq Substitute** — choosing a Stratix 10 SX ($5,000) over a ZCU102 ($3,200) for ARM + FPGA SoC work when you don't need Intel-specific hard IP; the Zynq ecosystem has far more open-source support
- **The Agilex 5 for Budget SoC** — the Agilex 5 E-Series DK costs $3,000; if you just need ARM + FPGA, a KRIA KV260 at $250 provides a similar experience at 1/12th the cost

---

## Pitfalls

1. **Alveo requires a server-class host** — PCIe Gen3 x16 needs a proper server with adequate power and cooling; desktop PCs may not provide enough PCIe slot power
2. **Zynq boot is complex** — FSBL → PMU firmware → ATF → U-Boot → Linux; a mistake in any stage bricks the board until JTAG recovery
3. **KRIA SOM availability** — the K26 SOM is sometimes out of stock; buy the complete starter kit, not the SOM alone
4. **Vivado license requirements** — Zynq UltraScale+ and Alveo require paid Vivado licenses; WebPACK does not support these devices
5. **HBM thermal constraints** — Alveo U50/U280 HBM generates significant heat; ensure your server has adequate airflow
6. **Quartus Pro license expires** — Intel dev kits include a 1-year Quartus Prime Pro license; after that, you must purchase a renewal (~$3,000–$5,000/year) or lose access to the tool
7. **Intel HPS boot complexity** — Stratix 10 SX and Agilex 5 HPS boot sequences (Preloader → U-Boot → Linux) are less documented than Zynq; the Yocto/Angstrom build process is fragile
8. **Intel transceiver tile routing** — Agilex 7 R-Tile/F-Tile/E-Tile have specific routing constraints; transceiver assignments must be planned early in the design

---

## Use Cases

- **ML inference in data centers** — Alveo + FINN for sub-microsecond inference
- **Network function acceleration** — Alveo + Open NIC for SmartNIC applications
- **Video analytics** — KV260 + Vitis-AI for smart camera applications
- **Software-defined radio** — ZCU104/VCU118 with FMC ADC/DAC cards
- **Robotics control** — KR260 + ROS 2 + FPGA motor control
- **High-frequency trading** — Alveo U280 with HBM for microsecond-level feed processing
- **CXL / PCIe 5.0 acceleration** — Agilex 7 I-Series + OPAE for cache-coherent host acceleration
- **112G optical networking** — Agilex 7 F-Series with E-Tile PAM4 transceivers
- **Intel SoC Linux + FPGA** — Stratix 10 SX with Yocto Linux on HPS, Agilex 5 with A76/A55

---

## References

- [Xilinx Alveo Platform](https://www.xilinx.com/products/boards-and-kits/alveo.html)
- [XRT Runtime (GitHub)](https://github.com/Xilinx/XRT) — open-source
- [KRIA KV260](https://www.xilinx.com/products/som/kria/kv260-vision-starter-kit.html)
- [PYNQ Project](http://www.pynq.io/) — Python + Zynq
- [Zynq UltraScale+ Technical Reference Manual (UG1085)](https://www.xilinx.com/support/documentation/user_guides/ug1085-zynq-ultrascale-trm.pdf)
- [Intel Agilex 7 F-Series Development Kit](https://www.altera.com/products/devkit/po-3033/agilex-7-fpga-f-series-development-kit-p-tile-and-e-tile-rev)
- [Intel Agilex 7 I-Series Development Kit](https://www.altera.com/products/devkit/po-3012/agilex-7-fpga-i-series-development-kit-2x-r-tile-and-1x-f-tile)
- [Stratix 10 SX SoC Development Kit](https://www.altera.com/products/devkit/po-3031/stratix-10-sx-soc-development-kit)
- [Agilex 5 E-Series Premium Development Kit](https://www.altera.com/products/devkit/po-3002/agilex-5-fpga-and-soc-e-series-premium-development-kit-es)
- [OPAE SDK (GitHub)](https://github.com/OFS/opae-sdk) — open-source Intel FPGA runtime
- [Hobbyist Boards](../12_open_source_open_hardware/open_boards/hobbyist_boards.md) — affordable open-toolchain boards
- [Repurposed Boards](repurposed_boards.md) — commercial hardware at low cost
