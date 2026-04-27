[← Home](../README.md) · [00 — Overview](README.md)

# History of FPGA Technology — From XC2064 to 3D Heterogeneous Integration

The FPGA was born in 1984 when Ross Freeman at Xilinx proposed a radical idea: a chip filled with programmable logic blocks and a reconfigurable interconnect, allowing customers to "re-wire" the silicon after manufacture. Nobody believed it would work. By 1992, it was a billion-dollar industry. This article traces the architectural evolution of FPGAs — from the first 64-LUT XC2064 through the modern chiplet-based Versal and Agilex families.

---

## Overview

FPGA history divides into four eras: **invention** (1984–1995): SRAM-based LUTs with manual schematic entry; **consolidation** (1995–2005): synthesis tools, hard multipliers, and embedded block RAM; **embedded processing** (2005–2015): hard CPU cores, multi-gigabit transceivers, and 28nm planar scaling; and **heterogeneous integration** (2015–present): 2.5D/3D stacking, AI engines, NoC interconnects, and open-source toolchains. Each era was enabled by process technology, but driven by the applications that FPGA customers demanded — first glue logic, then signal processing, then embedded systems, and now AI acceleration at scale.

---

## Era 1: Invention (1984–1995) — Proof of Life

### XC2064 (1985) — The First FPGA

| Parameter | XC2064 (Xilinx, 1985) | Modern Comparison (iCE40) |
|---|---|---|
| **Process** | 2 μm CMOS | 40 nm LP CMOS |
| **Logic cells** | 64 CLBs × 4-input LUTs | 5,280 LUT4s |
| **Flip-flops** | 128 | 5,280 |
| **Maximum gates** | 1,200 | ~1M equivalent |
| **Configuration** | External PROM | SPI flash |
| **Clock speed** | ~10 MHz | ~48 MHz |
| **Price (then)** | $55 (1985 ≈ $160 today) | $1.50 |

The XC2064 used a 4-input LUT with a single flip-flop. The interconnect was a simple island-style mesh — CLBs in a grid, connected by programmable switch matrices. Critically, Ross Freeman's insight was that **SRAM-based configuration** (not anti-fuse, not mask-ROM) would allow unlimited reprogramming — a bet his own board of directors thought was doomed because SRAM is volatile.

### Altera EP300 (1984) — CPLD, Not FPGA

Altera (founded 1983) initially shipped CPLDs — chips with a programmable AND-OR array and macrocells, closer to evolved PALs than modern FPGAs. Altera wouldn't ship a true LUT-based FPGA until the FLEX 8000 in 1992.

### Actel (1985) — Anti-Fuse FPGA

Actel (now Microchip FPGA) took the opposite approach: one-time programmable anti-fuse technology. No SRAM, no bitstream — just blown fuses that created permanent connections. This was radiation-hard by nature (no SRAM to flip) and instant-on (no configuration time), but not reconfigurable.

| Approach | Vendor | Reconfigurable | Volatile | Radiation tolerant |
|---|---|---|---|---|
| **SRAM** | Xilinx, Altera (later), Lattice (later) | Yes | Yes, needs external flash | No (SEU flips LUTs) |
| **Anti-fuse** | Actel, QuickLogic | No (OTP) | No | Yes (no SRAM) |
| **Flash** | Actel ProASIC (later), Microchip PolarFire | Yes | No (non-volatile) | Yes (flash cells immune) |
| **EPROM** | Altera MAX | Yes (UV erasable) | No | Partial |

---

## Era 2: Consolidation (1995–2005) — From Schematics to Synthesis

### The Synthesis Revolution

Until ~1995, FPGA designs were entered as schematics — literally drawing NAND gates. The shift to HDL (Verilog, VHDL) and logic synthesis (Synopsys Design Compiler, then Synplify, XST) transformed FPGA development from circuit design to software engineering. The same RTL could target ASICs and FPGAs — a crucial advantage that made FPGAs the prototyping platform for ASIC design.

### Hard Multipliers and Block RAM

| Innovation | First Introduced | Year | Why It Mattered |
|---|---|---|---|
| **Block RAM** | Xilinx Virtex (18 Kb) | 1998 | Before BRAM, all memory was LUT-based — 16 bits per LUT. BRAM gave 64× density |
| **Hard 18×18 multiplier** | Xilinx Virtex-II | 2000 | LUT-based 18×18 = ~300 LUTs. Hard multiplier = 1 DSP48. Signal processing became practical |
| **Multi-gigabit transceiver** | Xilinx Virtex-II Pro (RocketIO) | 2002 | First FPGA with 3.125 Gbps SERDES — enabled FPGA-based networking |
| **Embedded PowerPC 405** | Xilinx Virtex-II Pro | 2002 | First hard CPU in FPGA fabric — ahead of its time. PowerPC was niche; ARM would win later |

### Altera Stratix (2002) — The Counter-Attack

Altera's Stratix family introduced the **TriMatrix memory architecture** (M512, M4K, M-RAM blocks of different sizes) and the first digital signal processing (DSP) blocks with dedicated multipliers. Stratix established Altera as Xilinx's only serious competitor — a duopoly that persists today.

---

## Era 3: Embedded Processing (2005–2015) — CPUs Enter the Fabric

### Zynq (2011) — The FPSoC Emerges

Zynq-7000 integrated a dual-core ARM Cortex-A9 with FPGA fabric on the same die, sharing cache-coherent access to common DDR memory via the ACP (Accelerator Coherency Port). This was the inflection point: FPGAs stopped being "programmable glue logic" and became **heterogeneous computing platforms**.

| SoC FPGA | Year | CPUs | FPGA Fabric | Key Innovation |
|---|---|---|---|---|
| **Xilinx Zynq-7000** | 2011 | Dual Cortex-A9 | 28nm 7-series | ACP cache coherency, PCAP config |
| **Altera Cyclone V SoC** | 2012 | Dual Cortex-A9 | 28nm Cyclone V | HPS-to-FPGA AXI bridges |
| **Altera Arria 10 SoC** | 2014 | Dual Cortex-A9 | 20nm Arria 10 | PCIe Gen3 integrated |
| **Xilinx Zynq MPSoC** | 2015 | Quad A53 + dual R5F + GPU | 16nm UltraScale+ | Heterogeneous compute, hypervisor |
| **Microchip PolarFire SoC** | 2021 | 4× U54 + 1× E51 (RISC-V) | 28nm SONOS flash | First hard RISC-V FPGA SoC |
| **Intel Agilex SoC** | 2021 | Quad A53 (ARM) | Intel 7 | Chiplet, AI tensor DSPs |

### Intel Acquires Altera (2015)

Intel's $16.7B acquisition of Altera was the largest semiconductor deal at the time. The thesis: FPGAs would become accelerators alongside Xeon CPUs in the data center. This thesis is still playing out — Intel's FPGA revenue has been mixed, but the Agilex family is Intel's most serious data center FPGA yet.

---

## Era 4: Heterogeneous Integration (2015–Present)

### Beyond Monolithic Silicon

| Technology | Vendor | Description |
|---|---|---|
| **SSI (Stacked Silicon Interconnect)** | Xilinx | Multiple FPGA dies on a silicon interposer (Virtex-7 2000T, 2011). Sidesteps reticle limit |
| **EMIB (Embedded Multi-die Interconnect Bridge)** | Intel | Tiny silicon bridges embedded in the package substrate connecting dies. Lower cost than interposer |
| **CoWoS (Chip-on-Wafer-on-Substrate)** | TSMC | Used by Xilinx Versal. HBM stacks + FPGA dies on interposer |
| **HBM Integration** | Xilinx Virtex UltraScale+ HBM (2017), Intel Stratix 10 HBM (2018) | 8 GB HBM2 on-package. 460 GB/s bandwidth to FPGA fabric |
| **3D Logic-on-Logic** | Xilinx Virtex-7 HT (2012) | Two FPGA dies stacked face-to-face; microbumps connect logic directly |

### Versal ACAP (2019)

Versal adds **AI Engines** — 400-tile VLIW SIMD arrays (~4 TFLOPS) — and a **2D Network-on-Chip (NoC)** connecting all hard IP blocks via a routed packet network rather than traditional FPGA routing. Versal is not "an FPGA with AI bolted on" — it's a new class of device (ACAP: Adaptive Compute Acceleration Platform) where AI engines, FPGA fabric, ARM CPUs, and NoC are peers.

### Open-Source FPGA Toolchains

| Milestone | Year | Impact |
|---|---|---|
| **Project Icestorm** | 2015 | First fully open-source FPGA flow (iCE40). Proved it was possible |
| **Project Trellis** | 2019 | Open-source flow for ECP5, the first mid-range device with open tools |
| **SymbiFlow / F4PGA** | 2019–2022 | Xilinx 7-series + QuickLogic open-source flows |
| **Project Apicula** | 2022 | Gowin LittleBee and Arora nextpnr support |
| **LiteX** | 2018+ | Python-based SoC builder targeting open-source toolchains |

### RISC-V in FPGAs

| Milestone | Year | Impact |
|---|---|---|
| **PicoRV32** | 2015 | Minimal RISC-V soft core: 750–2,000 LUTs. Spurred RISC-V + FPGA movement |
| **VexRiscv** (SpinalHDL) | 2017 | Configurable RISC-V with Linux MMU, caches. Runs Linux on ECP5/Artix-7 |
| **PolarFire SoC** (Microchip) | 2021 | First FPGA with hard RISC-V cores |
| **MicroBlaze-V** (Xilinx) | 2023 | RISC-V soft processor replacing MicroBlaze (proprietary ISA) |

---

## Competitive Landscape: The FPGA Wars

### Major Acquisitions

| Year | Target | Acquirer | Price | Rationale |
|---|---|---|---|---|
| 1999 | Vantis (AMD PLD) | Lattice | $500M | Lattice enters CPLD market |
| 2010 | Actel | Microsemi | $430M | Flash FPGA + aerospace portfolio |
| 2015 | Altera | Intel | $16.7B | Data center FPGA acceleration |
| 2018 | Microsemi | Microchip | $8.35B | Flash FPGA + RISC-V + aerospace |
| 2022 | Xilinx | AMD | $49B | Data center + AI + adaptive compute |
| 2022 | Open-Silicon (eASIC) | Intel | N/A | Structured ASIC for FPGA-to-ASIC migration |

### Market Share (2024 Estimates)

| Vendor | FPGA Revenue Share | Position |
|---|---|---|
| AMD/Xilinx | ~50% | Market leader in density, AI, data center |
| Intel/Altera | ~25% | Second in density, strong in data center |
| Lattice | ~10% | Leader in low-power, open-source |
| Microchip | ~8% | Leader in rad-hard, flash FPGA |
| Gowin | ~3% | Fastest-growing low-cost supplier |
| Others (Achronix, Efinix, QuickLogic, NanoXplore) | ~4% | Niche specialists |

---

## References

| Source | Description |
|---|---|
| Stephen M. Trimberger, "Three Ages of FPGAs: A Retrospective on the First 30 Years" | IEEE Solid-State Circuits Magazine, 2015 |
| Ross Freeman, "XC2064 Patent" | US Patent 4,870,302 (1989) |
| Xilinx "The First FPGA" | https://www.xilinx.com/about/first-fpga.html |
| [Vendor Comparison Matrix](vendor_comparison.md) | Current vendor landscape |
| [Technology Nodes](technology_nodes.md) | Process technology evolution |
| [Architecture: Fabric](../02_architecture/fabric/luts_and_clbs.md) | How modern LUTs compare to the XC2064 |
