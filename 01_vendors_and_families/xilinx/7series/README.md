[← Xilinx/AMD Home](../README.md) · [← Section Home](../../README.md)

# Xilinx 7-Series — 28nm Workhorse Generation

The 7-series unified Xilinx's product line around a common 28nm architecture and the Vivado Design Suite. It is still the most widely deployed FPGA generation and has growing open-source toolchain support.

---

## Architecture Commonality

All 7-series devices share these primitives:

| Primitive | Description |
|---|---|
| **6-LUT** | 2× 5-LUT fracturable, with dual flip-flop per slice |
| **Slice** | 4 LUTs + 8 FFs + carry chain + MUXF7/MUXF8 |
| **CLB** | 2 slices (8 LUTs total) |
| **Block RAM** | 36 Kb (dual 18 Kb halves), true dual-port, FIFO, ECC |
| **DSP48E1** | 25×18 multiply + 48-bit accumulator, pre-adder, cascade, pattern detect |
| **Clock Management** | MMCM (Mixed-Mode Clock Manager) + PLL |
| **IO** | SelectIO (LVDS, SSTL, HSTL, LVCMOS), ISERDES/OSERDES (up to 1,600 Mbps DDR) |
| **Configuration** | SPI, BPI, SelectMAP, JTAG; AES-256 bitstream encryption |
| **Toolchain** | Vivado (all), ISE (legacy, Artix-7/Kintex-7/Virtex-7 only) |

---

## Family Variants

| Family | Position | LEs | Block RAM | DSP Slices | Transceivers | PCIe | Key Use |
|---|---|---|---|---|---|---|---|
| **Spartan-7** | Low-cost | 6K–102K | 0.2–4.3 Mb | 10–160 | None | None | IO expansion, simple control, open-source target |
| **Artix-7** | Cost-optimized | 13K–215K | 0.9–12.8 Mb | 45–740 | 2–16× 6.6 Gbps | Gen2 ×1/×4 | General-purpose, Arty boards, LiteX support |
| **Kintex-7** | Mid-range | 65K–478K | 4.9–33.6 Mb | 240–1,920 | 8–32× 12.5 Gbps | Gen2 ×8 | Wireless, video, defense |
| **Virtex-7** | High-end | 582K–1,955K | 28.8–65.2 Mb | 1,260–3,600 | 36–96× 13.1/28 Gbps | Gen3 ×8 | ASIC prototyping, massive DSP |
| **Zynq-7000** | SoC (FPGA + ARM) | 23K–444K | 1.8–26.0 Mb | 80–2,020 | Up to 16× 12.5 Gbps | Gen2 ×4/×8 | Embedded Linux, closest to Cyclone V SoC |

---

## Zynq-7000 — The Cyclone V SoC Equivalent

Zynq-7000 is the Xilinx counterpart to Cyclone V SoC. Same dual Cortex-A9 ARM cores, same 28nm fabric, but with key differences:

| Criterion | Cyclone V SoC | Zynq-7000 |
|---|---|---|
| **CPU** | Dual Cortex-A9, 800–925 MHz | Dual Cortex-A9, 667–866 MHz |
| **Max LEs** | 301K | 444K (Z-7100) |
| **Max Block RAM** | 12.2 Mb (M10K) | 26.0 Mb (36Kb BRAM) |
| **Max DSP** | 342 multipliers | 2,020 DSP48E1 |
| **Fastest transceiver** | 6.144 Gbps | 12.5 Gbps |
| **PCIe** | Gen2 ×1/×4 | Gen2 ×4/×8 |
| **FPGA-HPS interface** | 3× AXI-3 bridges (H2F/F2H/LWH2F) + F2S | 9× AXI3 interfaces (2× S_AXI_HP, 4× S_AXI_GP, etc.) |
| **Cache coherency** | Limited (HPS only) | **ACP** — FPGA can snoop L2 cache |
| **Boot source** | SD/MMC, QSPI, NAND | SD/MMC, QSPI, NAND, NOR, JTAG |
| **Open flow** | No | No (partial Raptor efforts) |
| **Dev boards** | DE10-Nano ($108) | Zybo Z7 ($199), PYNQ ($199+) |

**ACP is the key architectural advantage of Zynq-7000.** The Accelerator Coherency Port lets FPGA logic maintain cache-coherent access to the Cortex-A9 L2 cache — no flush/invalidate dance needed. Cyclone V SoC has no equivalent: FPGA can only access HPS DDR through F2S bridges which bypass L1/L2 caches entirely.

---

## 7-Series vs Intel Cyclone V — Side by Side

| Criterion | 7-Series | Cyclone V |
|---|---|---|
| **Process** | 28nm | 28nm |
| **LUT structure** | 6-input fracturable LUT (2 slices/CLB) | ALM fracturable 6-input (10 ALMs/LAB) |
| **DSP** | DSP48E1 (25×18) | Variable-precision (18×18 or 27×27) |
| **Block RAM** | 36 Kb BRAM | 10 Kb M10K |
| **CLB density** | 8 LUTs per CLB | 20 LUTs equivalent per LAB |
| **4G/5G transceivers** | Yes (Artix/Kintex/Virtex) | Yes (GX/GT variants) |
| **SoC hash coherency** | Zynq-7000 ACP | None |
| **FOSS toolchain** | Project X-Ray + SymbiFlow / F4PGA | None |

---

## Best Practices

1. **Spartan-7 for pure fabrication-cost-optimized designs** — lowest Xilinx entry point, good for open-source tooling targets.
2. **Artix-7 as the general-purpose 7-series default** — good transceiver/LE balance, well-supported by Arty boards and LiteX.
3. **Zynq-7000 over Cyclone V SoC when ACP matters** — eliminates cache-management code in FPGA-accelerated Linux applications.

## Pitfall: PL Doesn't Power Up Automatically on Zynq-7000

The Programmable Logic power domain is off after PS boot. You must enable it explicitly via PS-side devcfg (/sys/class/fpga_manager/) or U-Boot. This differs from Cyclone V where the fabric is configured as part of the HPS boot sequence.

---

## Development Boards

### Xilinx / AMD (First-Party)

#### Spartan-7

| Board | FPGA | LUTs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **SP701 Eval Kit** | XC7S100 | 102K | FMC, DDR3, GbE, HDMI, QSPI | ~$395 | Only official Spartan-7 full-featured board |

#### Artix-7

| Board | FPGA | LUTs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **Arty A7-100T** | XC7A100T | 101K | Arduino/chipKIT headers, DDR3, GbE, QSPI, Pmod | ~$249 | General Artix-7 workhorse, LiteX-friendly |
| Arty A7-35T | XC7A35T | 33K | Same form-factor as A7-100T, smaller FPGA | ~$129 | Entry-level Artix-7, budget-constrained |
| Nexys A7-100T | XC7A100T | 101K | 7-seg ×8, VGA, audio, USB HID, switches/buttons, Pmod | ~$319 | University/teaching, digital logic lab |
| Basys 3 | XC7A35T | 33K | 7-seg, VGA, USB HID, switches, Pmod, breadboard-friendly | ~$149 | Intro FPGA course, hobbyist |
| Cmod A7 | XC7A35T | 33K | DIP-48 breadboard form-factor, SRAM, QSPI | ~$89 | Breadboard FPGA, smallest Artix-7 |

#### Kintex-7

| Board | FPGA | LUTs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **KC705 Eval Kit** | XC7K325T | 326K | FMC HPC/LPC ×2, DDR3, GbE, PCIe Gen2 ×8 edge, SMA clock | ~$1,695 | Mid-range transceiver & DSP eval |

#### Virtex-7

| Board | FPGA | LUTs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **VC707 Eval Kit** | XC7VX485T | 485K | FMC ×2, DDR3, GbE, PCIe Gen3 ×8 edge, QSFP cage | ~$3,495 | High-end Virtex-7 eval |

#### Zynq-7000

| Board | FPGA | LUTs | CPU | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|---|
| **Zybo Z7-20** | XC7Z020 | 53K | Dual A9 @ 667 MHz | HDMI in/out, audio codec, Pmod ×6, Arduino header | ~$199 | General Zynq dev, closest to DE10-Nano |
| Zybo Z7-10 | XC7Z010 | 28K | Dual A9 @ 667 MHz | Same form-factor, smaller FPGA | ~$149 | Entry-level Zynq |
| **PYNQ-Z2** | XC7Z020 | 53K | Dual A9 @ 650 MHz | HDMI in/out, audio, Arduino, RPi header, Pmod ×2 | ~$199 | Python FPGA framework (PYNQ), education |
| ZedBoard | XC7Z020 | 85K | Dual A9 @ 667 MHz | FMC, HDMI out, VGA, audio, GbE, OLED display | ~$349 | Classic Zynq development, widely documented |
| ZC702 Eval Kit | XC7Z020 | 85K | Dual A9 @ 667 MHz | FMC ×2, GbE, HDMI, PCIe, XADC header | ~$895 | Official Xilinx Zynq eval |
| ZC706 Eval Kit | XC7Z045 | 350K | Dual A9 @ 1 GHz | FMC ×2, GbE, HDMI, PCIe Gen2 ×8, GTH XCVR | ~$2,495 | High-end Zynq: 350K LEs + 12.5G transceivers |
| Cora Z7-07S | XC7Z007S | 23K | Single A9 @ 667 MHz | Arduino/chipKIT form-factor, Pmod, USB-powered | ~$99 | Cheapest Xilinx SoC board |

### Third-Party / Community

| Board | FPGA | LUTs | Key Feature | Approx. Price | Best For |
|---|---|---|---|---|---|
| **Trenz TE0720 SoM** | XC7Z020 | 85K | SODIMM form-factor, 1 GB DDR3, industrial temp option | ~$150 | Embedded Zynq deployment, custom carrier |
| QMTech Zynq-7000 | XC7Z020 | 85K | Bare board, DDR3 SODIMM, HDMI | ~$60–100 | Cheapest Zynq-7000 development alternative |
| Arty Z7 (community) | XC7Z020 | 53K | Arduino Zynq hybrid | ~$229 | Similar to Zybo, PYNQ-compatible |

### Choosing a Board

| You want... | Get... |
|---|---|
| Closest to Cyclone V SoC / DE10-Nano experience | Zybo Z7-20 (~$199) or ZC702 |
| Python FPGA development (PYNQ) | PYNQ-Z2 (~$199) |
| Cheapest Xilinx SoC | Cora Z7-07S (~$99) |
| Pure FPGA, no ARM | Arty A7-100T (~$249) or Basys 3 (~$149) |
| University digital logic course | Nexys A7 or Basys 3 |
| High-end Zynq dev (350K LEs + transceivers) | ZC706 (~$2,495) |
| Kintex-7 transceiver evaluation | KC705 (~$1,695) |
| Budget Zynq from China | QMTech Zynq-7000 (~$60–100) |

---

## References

| Source | Path |
|---|---|
| 7-series Data Sheets (DS180–DS191) | AMD/Xilinx documentation |
| Zynq-7000 TRM (UG585) | AMD/Xilinx documentation |
