[← Home](../README.md) · [00 — Overview](README.md)

# FPGA Market Landscape — When to Choose FPGA vs ASIC vs MCU

Not every hardware problem needs an FPGA. A well-chosen microcontroller is cheaper, faster to develop, and consumes less power. An ASIC wins at volume. This article maps the decision landscape — when an FPGA is the right tool, when it's overhead, and which class of FPGA matches each application domain.

---

## Overview

FPGAs occupy a unique niche between software-programmable microcontrollers (MCUs/CPUs) and fixed-function silicon (ASICs). They offer hardware-level parallelism and determinism without the NRE costs of chip fabrication, but at a per-unit cost 10–100× higher than an equivalent MCU and 2–10× higher than a mature ASIC. The sweet spot: applications requiring **reconfigurability, hardware-level I/O determinism, or parallel processing** at volumes below ~1M units — where ASIC NRE ($5M–$50M) cannot be amortized. The FPGA market spans from $2 iCE40 devices handling simple glue logic to $100K+ Versal Premium devices accelerating AI inference in data centers.

---

## FPGA vs ASIC vs MCU: Decision Matrix

| Criterion | MCU / CPU | FPGA | ASIC |
|---|---|---|---|
| **Unit cost** (100 K units) | $0.50–$15 | $2–$5,000 | $0.10–$50 (after NRE) |
| **NRE / development cost** | $0 (free toolchains) | $0–$5,000 (IP licenses) | $5M–$50M (masks + validation) |
| **Power consumption** | μW–mW (sleep: nW) | mW–W (no useful sleep) | μW–W (optimized for task) |
| **Parallelism** | Limited (cores × SIMD) | Massive (spatial) | Unlimited (custom datapaths) |
| **Deterministic I/O** | μs–ms jitter | ns determinism | ns determinism |
| **Reconfigurability** | Software (microsecond) | Hardware (millisecond partial, second full) | None (fixed at fab) |
| **Time to market** | Weeks | Months | Years |
| **Flexibility post-deployment** | Full (OTA firmware) | Partial (OTA bitstream) | None |
| **Volume sweet spot** | 1–10M+ | 1–100K | 1M+ |

### When the FPGA Wins

| Scenario | Why FPGA Over MCU | Why FPGA Over ASIC |
|---|---|---|
| **Real-time control (motor, power converter)** | MCU interrupt latency: 1–100 μs. FPGA: single-cycle (5–10 ns) | Volumes too low (<100K) for ASIC |
| **Protocol bridging (10 protocols → USB)** | Software bit-banging limits throughput | Protocol mix changes; ASIC would need to anticipate all |
| **Data acquisition (>1 GSPS)** | MCUs max at 10s of MSPS | FPGA transceivers at 58 Gbps without ASIC NRE |
| **AI inference at edge (<10 ms latency)** | MCU: seconds per inference. GPU: too much power | Volumes and architecture evolving too fast |
| **Retro computing / hardware preservation** | Software emulation lacks hardware accuracy | FPGA matches original timing at gate level |

### When the MCU / ASIC Wins

| Scenario | Better Choice | Why |
|---|---|---|
| **BLE sensor tag ($2 BOM)** | MCU (nRF52) | FPGA overkill in cost and power |
| **Smartphone application processor** | ASIC (Snapdragon, Apple Silicon) | 100M+ volume amortizes NRE |
| **Simple PID controller (100 Hz loop)** | MCU (STM32) | 100 Hz is trivial for any MCU; FPGA adds cost, complexity |
| **Ethernet switch (fixed-function)** | ASIC (Broadcom, Marvell) | Mature, cheap, optimized ASICs exist |

---

## FPGA Market Segments

### Low-End (<$10 chip, <25K LUTs)

| Use Case | Typical Devices | Volume |
|---|---|---|
| Glue logic, voltage translation | iCE40, MachXO2, MAX 10 | 10K–1M+ |
| Consumer electronics control | Gowin LittleBee, iCE40 | 50K–500K |
| IoT sensor hub | QuickLogic EOS S3 | 10K–100K |
| CPLD replacement | MachXO2, MAX V | 50K–500K |

**Key vendors:** Lattice, Gowin, Intel (MAX 10)

### Mid-Range ($10–$200 chip, 25K–500K LUTs)

| Use Case | Typical Devices | Volume |
|---|---|---|
| Industrial motor control | Artix-7, Cyclone V, ECP5 | 1K–50K |
| Video processing / broadcast | Kintex-7, Arria 10 | 1K–10K |
| Software-defined radio | Zynq-7000, Cyclone V SoC | 1K–10K |
| Retro computing | Cyclone V (DE10-Nano) | 5K–50K |
| Open-source Linux SoC | ECP5 (LiteX + VexRiscv) | 100–5K |

**Key vendors:** Xilinx (7-series), Intel (Cyclone V, Arria 10), Lattice (ECP5)

### High-End ($200–$5,000 chip, 500K–5M LUTs)

| Use Case | Typical Devices | Volume |
|---|---|---|
| 5G wireless infrastructure | UltraScale+ RFSoC, Agilex 7 | 1K–10K |
| AI/ML inference acceleration | Versal AI, Stratix 10 | 1K–5K |
| High-frequency trading | Virtex UltraScale+, Agilex 7 | 100–1K |
| Military/defense signal processing | Virtex, Stratix 10 | 100–500 |

**Key vendors:** Xilinx (UltraScale+, Versal), Intel (Stratix 10, Agilex 7/9)

### Specialized

| Segment | Devices | Key Feature |
|---|---|---|
| Aerospace / radiation-tolerant | RT PolarFire, NanoXplore | SEU immune, >100 Krad TID |
| Automotive (ADAS, infotainment) | Zynq UltraScale+, Cyclone V | AEC-Q100, ISO 26262 |
| Medical imaging | Kintex UltraScale+, PolarFire | Low power, high DSP density |
| Data center SmartNIC | Versal Premium, Agilex 7 | 100–400G Ethernet, PCIe Gen5 |

---

## Technology Trends Shaping the Market

### 1. Hardened CPU+FPGA SoCs

Zynq (2011) proved that integrating ARM Cortex-A CPUs with FPGA fabric on the same die addresses >50% of embedded FPGA use cases. Now SoC FPGAs span from Cortex-A9 (Zynq-7000) to heterogeneous quad A53 + dual R5F + GPU (Zynq MPSoC) to 5× hard RISC-V cores (PolarFire SoC). The trend: **more CPU heterogeneity, not just faster CPUs**.

### 2. AI Engines and Tensor Acceleration

Versal AI Engines (Xilinx) and Agilex Tensor DSPs (Intel) represent a new category — not CPUs, not FPGAs, but **coarse-grained reconfigurable arrays** optimized for matrix multiply. They deliver 10–100× the AI throughput of traditional FPGA DSP fabric at the cost of less flexibility.

### 3. Open-Source Toolchains

The Yosys+nextpnr ecosystem (iCE40 since 2015, ECP5 since 2019, Gowin since 2022) means FPGA entry now costs $0 in software licenses. Projects like LiteX, Amaranth/nMigen, and SpinalHDL make FPGA development accessible to software engineers. The open-source FPGA movement follows the same trajectory as open-source compilers (GCC → LLVM) — from niche to production.

### 4. Chiplet and 2.5D/3D Integration

Intel EMIB, Xilinx SSI, and TSMC CoWoS stack multiple silicon dies in one package. This allows mixing process nodes (e.g., 7nm FPGA fabric + 14nm transceivers + HBM memory) and scaling beyond the reticle limit. Versal Premium and Agilex 9 are fundamentally chiplet-based.

---

## When to Migrate from FPGA to ASIC

| Trigger | Action |
|---|---|
| Volume > 100K units/year | ASIC cost amortization becomes favorable |
| Power budget < 100 mW | FPGA static power (100–500 mW) is too high; ASIC can be optimized to μW |
| Design is stable for >12 months | ASIC requires 18–24 months to fabricate; FPGA flexibility no longer needed |
| Unit cost dominates | ASIC unit cost is 1/5–1/20 of FPGA at volume |

---

## References

| Source | Document |
|---|---|
| [Vendor Comparison Matrix](vendor_comparison.md) | Side-by-side vendor comparison across six dimensions |
| [History of FPGA Technology](history.md) | From XC2064 to modern 3D FPGAs |
| [Technology Nodes](technology_nodes.md) | Process technology impact on FPGA characteristics |
| [Vendors & Families](../01_vendors_and_families/README.md) | Per-vendor device family guides |
