[← Section Home](../README.md) · [← Project Home](../../README.md)

# 01-E — Microchip (formerly Microsemi/Actel)

Flash-based and anti-fuse FPGA specialist with a lineage stretching back to Actel (founded 1985). Acquired by Microsemi in 2010, then by Microchip in 2018. Microchip's PolarFire and SmartFusion families offer low-power, radiation-tolerant, and SEU-immune options — with the industry's only hard RISC-V CPU ecosystem (Mi-V). Flash-based configuration means instant-on (<1 ms), no external bitstream to intercept, and near-zero standby power.

---

## Flash FPGA: A Fundamentally Different Technology

Unlike SRAM FPGAs (Intel, Xilinx, Lattice) that lose configuration at power-off and must reload from external flash, Microchip FPGAs store configuration in on-die non-volatile memory:

| Property | SRAM FPGA | Microchip Flash FPGA |
|---|---|---|
| Configuration storage | External QSPI chip | Internal SONOS flash cells |
| Boot time | 50–500 ms | **<1 ms** instant-on |
| SEU susceptibility | High (SRAM cell flips in radiation) | **Immune** (flash cell doesn't disturb) |
| Standby power | High (SRAM leakage current) | Near-zero |
| Bitstream security | Encryption with key in eFuse/BBRAM | **Inherent** — no external bitstream to intercept |
| Reprogramming cycles | Unlimited (external flash wears) | 500–1,000 cycles (flash endurance) |
| Live-at-power-up IO | No (tri-stated until configured) | Yes (flash loads in <1 ms) |

---

## Technology Platforms

| Platform | Process | Families | Key Features |
|---|---|---|---|
| **PolarFire** | 28nm SONOS | MPF100–500 (FPGA), MPFS (SoC w/ RISC-V) | Mid-range flash FPGA, 100K–482K LEs, 12.7G SERDES, PCIe Gen2. SoC: 5× RISC-V cores |
| **RT PolarFire** | 28nm SONOS-RT | RTPF | Radiation-tolerant: >100 Krad TID, no SEL up to LET >63, −40°–125°C |
| SmartFusion2 | 65nm flash | M2S | Hard Cortex-M3 (166 MHz), 12-bit ADC, FIPS 140-2 crypto, anti-tamper |
| IGLOO2 | 65nm flash | M2GL | Same 65nm fabric as SmartFusion2, without MCU or analog blocks |

---

## Family Directories

| Directory | Coverage |
|---|---|
| [polarfire/](polarfire/README.md) | **PolarFire (28nm SONOS)** — FPGA-only (100K–482K LEs, 12.7G SERDES, PCIe Gen2) + **[PolarFire SoC](polarfire/soc/README.md)**: 5× hard RISC-V cores (4× U54 + E51, Linux-capable, 64-bit RV64IMAFDC). Coherent-by-default AXI4 switch, no cache flushes needed. RT PolarFire (radiation-tolerant, >100 Krad). Instant-on <1 ms, SEU immune |
| [smartfusion2_igloo2/](smartfusion2_igloo2/README.md) | **SmartFusion2 & IGLOO2 (65nm flash)** — SmartFusion2: hard Cortex-M3 + 12-bit ADC + FIPS 140-2 crypto (anti-tamper, zeroization). IGLOO2: same fabric without MCU/analog. Defense and secure embedded |

---

## Family Comparison

| Family | Process | LEs (max) | CPU | SERDES | Key Differentiator | Price Range |
|---|---|---|---|---|---|---|
| PolarFire MPF100T | 28nm SONOS | 109K | None | 12.7 Gbps (×8) | Entry flash FPGA, lowest cost PolarFire | $20–80 |
| PolarFire MPF500T | 28nm SONOS | 482K | None | 12.7 Gbps (×24) | Highest flash FPGA density, eSRAM | $100–500 |
| **PolarFire SoC** | 28nm SONOS | 460K | 4× U54 + E51 (RISC-V) | 12.7 Gbps (×8) | Only RISC-V hard-SoC FPGA in industry | $50–500 |
| RT PolarFire | 28nm SONOS-RT | ~300K | 4× U54 + E51 (RISC-V) | 12.7 Gbps | >100 Krad, −40°–125°C, SEL immune | $2K–20K+ |
| SmartFusion2 | 65nm flash | 150K | Cortex-M3 @ 166 MHz | None | FIPS 140-2, 12-bit ADC, anti-tamper | $15–200 |
| IGLOO2 | 65nm flash | 150K | None | None | Flash FPGA without MCU, cost-optimized | $10–100 |

---

## Development Board Highlights

| Board | Family | Key Spec | Price | Best For |
|---|---|---|---|---|
| **PolarFire SoC Icicle Kit** | MPFS250T | 254K LEs, 4× U54 + E51, PCIe Gen2, GbE, mikroBUS | ~$499 | RISC-V Linux SoC FPGA development |
| PolarFire SoC Discovery Kit | MPFS095T | 95K LEs, 4× U54 + E51, mikroBUS, RPi header, USB | ~$132 | Cheapest RISC-V SoC FPGA entry |
| PolarFire Eval Kit | MPF300T | 300K LEs, PCIe Gen2, DDR4, FMC, GbE | ~$499 | Pure FPGA evaluation |
| SmartFusion2 Eval Kit | M2S150 | Cortex-M3, ADC, crypto, FMC | ~$399 | Secure embedded prototyping |
| Sundance V3 SoM | MPFS250T | SODIMM SoM, DDR4, GbE, production-ready | ~$600+ | Production RISC-V SoC deployment |

---

## Best Practices

1. **PolarFire SoC for RISC-V Linux + FPGA** — the only FPGA with 5 hard RISC-V cores running mainline Linux. Coherent-by-default means zero cache management code in your FPGA accelerators.
2. **RT PolarFire for space applications** — if your design flies above LEO or in high-radiation environments, RT PolarFire's >100 Krad TID rating and SEL immunity make it the go-to choice.
3. **SmartFusion2 when you need FIPS 140-2** — validated cryptographic boundary with anti-tamper and zeroization. No other FPGA vendor offers this level of security certification at this price point.
4. **Plan around 500–1,000 flash programming cycles** — enough for 2–3 years of daily prototyping, but not for continuous reconfiguration. Use SRAM FPGAs during development, switch to Microchip for production.
5. **Libero SoC is free but TCL-dependent** — the GUI lags behind Vivado and Quartus. Expect to script your flow. Libero's SmartDesign (block-diagram IP integration) is its best feature.

## Pitfalls

1. **Flash endurance is limited** — 500–1,000 guaranteed cycles. A CI pipeline that reprograms an SRAM FPGA 50×/day works fine on Xilinx/Intel but will kill a Microchip flash FPGA in weeks.
2. **Libero SoC is Windows/Red Hat only** — no Ubuntu/Debian official support. Linux users may need VM or WSL workarounds.
3. **E51 monitor core is mandatory** — the E51 boots first, initializes the system, then hands off to U54 application cores. You cannot bypass HSS (Hart Software Services) for the initial boot sequence.
4. **PolarFire SERDES is 12.7 Gbps max** — fine for PCIe Gen2/Gen3, SATA 3, 10GbE, but not enough for 25G/100G networking. Use Xilinx or Intel for those.
5. **Smaller ecosystem than Intel/Xilinx** — fewer IP cores, less community content, fewer tutorials. The Mi-V RISC-V ecosystem is growing but still behind ARM-based SoC FPGA communities.

---

## References

| Source | Description |
|---|---|
| Microchip FPGA Documentation | https://www.microchip.com/en-us/products/fpgas-and-plds |
| PolarFire SoC User Guide (UG0820) | Definitive PolarFire SoC reference |
| Mi-V RISC-V Ecosystem | https://www.microchip.com/en-us/products/fpgas-and-plds/ip-cores/miv-risc-v |
| Libero SoC Design Suite | https://www.microchip.com/en-us/products/fpgas-and-plds/fpga-and-soc-design-tools/libero-software |
| Hart Software Services (HSS) | https://github.com/polarfire-soc/hart-software-services — reference boot monitor |
