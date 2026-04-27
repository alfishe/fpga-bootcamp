[← CPLD Home](README.md) · [← Architecture Home](../README.md) · [← Project Home](../../README.md)

# Non-Volatile Programmable Logic

Non-volatile programmable logic retains its configuration without continuous power. This category spans true CPLDs, flash-based FPGAs, antifuse devices, and SRAM-plus-flash hybrids. The common trait: **the device is functional immediately at power-on**.

---

## Technology Types

```
Non-Volatile Programmable Logic
│
├── Flash-Based
│   ├── CPLD (MAX V, MachXO2, ispMACH)
│   ├── Flash FPGA (MAX 10, MachXO3, ProASIC3)
│   └── SRAM+Flash Hybrid (Spartan-3AN, Lattice XP2)
│
├── Antifuse-Based
│   ├── One-Time Programmable (OTP)
│   └── Rad-Tolerant / Space-grade (RTAX-S, RT ProASIC3)
│
└── Emerging / Niche
    ├── SONOS (Microchip FPGA persistent cells)
    └── FeRAM / MRAM (experimental)
```

---

## Why Non-Volatile Logic Is a Niche Market

Despite the practical advantages of instant-on and zero standby power, non-volatile programmable logic commands a shrinking share of the programmable logic market. Several structural forces explain why most families are deprecated, discontinued, or relegated to ultra-niche segments.

### 1. Process Node Scaling Limitation

Flash transistors do not scale to advanced CMOS nodes. While SRAM FPGAs have moved to 7 nm (AMD Versal) and 10 nm (Intel Agilex), flash-based configuration cells are effectively stuck at 40–65 nm. This creates a **density ceiling** that makes non-volatile devices uncompetitive for large designs.

| Technology | Effective Process Node | Max Density | FPGA Equivalent |
|---|---|---|---|
| **Intel MAX V (CPLD)** | 180 nm | 1,270 LEs | — |
| **Intel MAX 10 (flash FPGA)** | 55 nm | 50K LEs | Cyclone V (40 nm) |
| **Lattice MachXO3 (flash FPGA)** | 65 nm | 9.4K LUTs | — |
| **Microchip PolarFire (SONOS)** | 28 nm | 500K LEs | Xilinx Artix-7 (28 nm) |
| **AMD Versal (SRAM)** | 7 nm | 2M+ LEs | — |

### 2. The External Flash Solution Is "Good Enough"

For the vast majority of designs, an SRAM FPGA + $0.50 QSPI flash is cheaper and more flexible than a flash-based FPGA. The configuration delay (50–200 ms) is acceptable for almost every application except safety-critical instant-on systems.

| Solution | Boot Delay | Cost | Flexibility |
|---|---|---|---|
| SRAM FPGA + QSPI | 50–200 ms | FPGA $20 + flash $0.50 | Unlimited reconfig |
| MAX 10 | 1–20 ms | $8–$25 | 10K cycles, internal |
| CPLD | 0 ms | $2–$15 | 10K cycles, tiny density |

**Market reality:** Engineers will tolerate a 100 ms boot to save $5 and get 10× the logic density.

### 3. Microcontrollers Ate the Glue-Logic Market

The core CPLD use case — bus bridging, level shifting, simple state machines — is now served by **32-bit microcontrollers** at $0.30–$2.00 (ARM Cortex-M0/M3). An STM32G0 can do I2C↔SPI bridging with firmware updates, DMA, and sleep modes at a fraction of the CPLD cost.

| Task | CPLD | MCU | Winner |
|---|---|---|---|
| I2C ↔ SPI bridge | MAX V $3 + no code | STM32G0 $1 + firmware | MCU (flexibility) |
| Power sequencing | CPLD $2, instant | MCU $0.50, 10 ms boot | Tie (CPLD for safety) |
| LED blinker | CPLD $2 | MCU $0.30 | MCU |
| 5V-tolerant logic | CPLD $3 | 5V MCU $1 | Tie (CPLD for speed) |

### 4. Major Vendor Exits

- **Xilinx/AMD:** Discontinued all CPLD families (XC9500XL, CoolRunner-II) in 2023–2024. No replacement announced.
- **Intel:** MAX V is the last true CPLD; no successor on the roadmap. MAX 10 (flash FPGA) continues but is marketed as a low-cost FPGA, not a CPLD replacement.
- **Lattice and Microchip** are the only vendors still actively investing in non-volatile programmable logic (MachXO3, CrossLink-NX, PolarFire).

### 5. Antifuse Is Ultra-Niche

Antifuse FPGAs are **3–10× more expensive** than equivalent SRAM FPGAs and are one-time programmable. They survive only in markets where radiation immunity or physical tamper resistance justifies the premium:

- Satellites and space probes
- Military avionics
- Nuclear reactor controls

Total addressable market: **< $100M annually** vs. **> $10B for SRAM FPGAs**.

---

## 1. Flash-Based

Flash-based programmable logic stores configuration in floating-gate transistors. It is **electrically erasable and reprogrammable** (typically 100–10,000 cycles).

### Flash CPLDs

| Family | Vendor | Density | Key Trait |
|---|---|---|---|
| MAX V | Intel | 40–1,270 LEs | 1.8V, lowest power |
| MachXO2 | Lattice | 256–7,000 LUTs | Instant-on, tiny WLCSP |
| ispMACH 4000 | Lattice | 32–512 macrocells | 3.3V/2.5V/1.8V |
| ATF15 | Microchip | 32–128 macrocells | 5V tolerant, industrial |

**Programming:** JTAG or in-system programming. Configuration is internal; no external PROM.

**Endurance:** 10,000 program/erase cycles typical. Not suitable for frequent reconfiguration.

### Flash FPGAs

These are architecturally FPGAs (LUT-based) but use flash for configuration storage.

| Family | Vendor | Density | Special Features |
|---|---|---|---|
| MAX 10 | Intel | 2K–50K LEs | Dual config, ADC, PLLs |
| MachXO3 | Lattice | 640–9,400 LUTs | Embedded flash, hardened I2C/SPI |
| ProASIC3 | Microchip | 3K–75K LEs | Flash + SRAM fabric, low power |
| PolarFire | Microchip | 100K–500K LEs | Flash-based, lowest static power in class |

**Advantage over SRAM FPGA:** No external configuration device, instant-on, lower standby power.

**Disadvantage:** Reprogramming wears flash; large arrays are slower to erase.

### SRAM + Flash Hybrids

These devices have an **SRAM FPGA fabric** but include an **on-chip flash** that automatically loads the SRAM at power-on.

| Family | Vendor | Flash Size | Notes |
|---|---|---|---|
| Spartan-3AN | Xilinx (obsolete) | 1–8 Mb | First Xilinx "safe" single-chip solution |
| LatticeXP2 | Lattice (legacy) | 1–2 Mb | Flash loads SRAM on boot; can reconfig SRAM live |
| iCE40 UltraPlus | Lattice | Internal NVM | Small NVM stores config for SRAM loading |

**How it works:**
1. At power-on, internal state machine copies flash → SRAM fabric
2. FPGA becomes operational (10–100 ms delay)
3. Flash can be updated via JTAG; SRAM can be reloaded without wearing flash

---

## 2. Antifuse-Based

Antifuse devices are **one-time programmable (OTP)**. An unprogrammed antifuse is an open circuit. Programming applies a high voltage that permanently creates a low-resistance connection.

### Characteristics

- **Non-volatile:** Configuration is permanent
- **Radiation-tolerant:** No floating gates to drift; immune to SEU (single-event upsets)
- **Secure:** Cannot be read back or reverse-engineered without destructive analysis
- **Higher density than CPLDs:** Up to 250K+ LEs in modern families

### Antifuse FPGA Families

| Family | Vendor | Density | Target Market |
|---|---|---|---|
| RTAX-S / RTAX-DSP | Microchip | 3K–250K LEs | Space, radiation-tolerant |
| RT ProASIC3 | Microchip | 3K–75K LEs | Radiation-tolerant flash+antifuse |
| SX-A / eX | Microchip (legacy Actel) | 1K–48K LEs | Military, aerospace |

**Where antifuse wins:**
- Satellites and deep-space probes (radiation immunity)
- Military systems (tamper resistance)
- Safety-critical avionics (configuration cannot corrupt)

**Trade-offs:**
- **OTP:** One shot — a mistake requires a new chip
- **Cost:** 3–10× more expensive than equivalent flash/SRAM FPGA
- **Power:** Higher static power than flash for equivalent density

---

## 3. Instant-On and Power-On Behavior

| Technology | Power-On Delay | Source | Reprogrammable |
|---|---|---|---|
| Flash CPLD | < 1 ms | Internal flash | Yes (10K cycles) |
| Flash FPGA (MAX 10) | 1–20 ms | Internal flash | Yes (dual config) |
| SRAM + Flash hybrid | 10–100 ms | On-chip flash → SRAM | Yes (flash), SRAM unlimited |
| Antifuse FPGA | < 1 ms | Permanent antifuse | **No (OTP)** |
| SRAM FPGA + external flash | 50 ms–2 s | External SPI/QSPI flash | Yes (external flash) |

**Critical insight:** Antifuse and flash CPLDs are the only technologies with true **zero-delay** instant-on. Flash FPGAs have a small delay (1–20 ms) while copying internal flash to SRAM configuration cells.

---

## 4. Security Implications

| Technology | Bitstream Extraction Risk | Countermeasures |
|---|---|---|
| SRAM FPGA + external flash | **High** — SPI flash easily read | AES bitstream encryption (Xilinx/Intel) |
| Flash FPGA / CPLD | **Medium** — JTAG readback possible | Security bit disables readback |
| Antifuse FPGA | **Very Low** — no bitstream stored | Physical destruction required |
| SRAM+Flash hybrid | **Medium** — same as flash | Security bit, AES optional |

**Best practice for high-security designs:**
1. Use bitstream encryption on SRAM FPGAs (Zynq, Stratix, etc.)
2. Set security fuse on flash CPLDs to disable readback
3. For tamper-proofing: antifuse FPGAs provide the highest physical security

---

## 5. Vendor Landscape Summary

| Vendor | Flash CPLD | Flash FPGA | Antifuse FPGA | SRAM+Flash Hybrid |
|---|---|---|---|---|
| **Intel** | MAX V | MAX 10 | — | — |
| **Lattice** | MachXO2, ispMACH | MachXO3, CrossLink-NX | — | XP2 (legacy) |
| **Microchip** | ATF15 | ProASIC3, PolarFire | RTAX-S, RT ProASIC3 | — |
| **Xilinx / AMD** | — (exited) | — | — | Spartan-3AN (obsolete) |

> **Xilinx/AMD no longer manufactures CPLDs or non-volatile FPGAs.** Designers requiring instant-on or non-volatile logic from the AMD ecosystem must use external configuration (QSPI flash) with bitstream encryption, or migrate to Intel/Lattice/Microchip families.

---

## Reference Development Boards

A curated list of development boards for non-volatile programmable logic families. Many legacy boards are discontinued but remain available through surplus channels.

### Flash CPLD / Small Flash FPGA Boards

| Board | Vendor | Price (USD) | Device | Key Features | Status |
|---|---|---|---|---|---|
| **MachXO2 Breakout Board** | Lattice | $126 | LCMXO2-7000HE | 7000 LUTs, 0.1" headers, prototyping area | Active |
| **MachXO3LF Starter Kit** | Lattice | $159 | LCMXO3LF-6900C | 6900 LUTs, LED array, USB prog, proto area | Active |
| **BeMicro MAX 10** | Arrow | ~$30 | 10M08DAF484C8G | 8 MB SDRAM, Pmod, accelerometer, DAC | Active |
| **MAX 10 Evaluation Kit** | Intel / Altera | $53 | 10M08SAE144C8G | 144-EQFP, power measurement, ADC, Arduino | Active |
| **DE10-Lite** | Terasic | $150 ($82 academic) | 10M50DAF484C7G | 64 MB SDRAM, VGA, Arduino, hex displays | Active |

### Flash FPGA (Mid-Range / High-End)

| Board | Vendor | Price (USD) | Device | Key Features | Status |
|---|---|---|---|---|---|
| **PolarFire Evaluation Kit** | Microchip | $1,887 | MPF300TS | PCIe, GigE, 6 GB RAM, 256 MB SPI flash | Active |
| **PolarFire SoC Icicle Kit** | Microchip | ~$500 | MPFS250T | RISC-V + PolarFire SoC, Linux-capable | Active |

### Discontinued / Legacy Boards

| Board | Vendor | Last Known Price | Device | Status | Notes |
|---|---|---|---|---|---|
| **Spartan-3AN Starter Kit** | Xilinx | N/A | XC3S700AN | **Discontinued** | Last Xilinx non-volatile FPGA board; replaced by SRAM + external flash |
| **CoolRunner-II Starter Kit** | Xilinx | N/A | XC2C256 | **Discontinued** | CPLD; no Xilinx successor |
| **MAX II / MAX V Eval Kit** | Intel / Terasic | N/A | 5M1270Z | **Discontinued** | True CPLD eval platform; superseded by MAX 10 FPGA kits |
| **RTAX-S Development Kit** | Microchip | ~$15,000+ | RTAX2000S | **Active (niche)** | Space-grade antifuse; restricted sales, long lead times |

> **Current as of: 2026-04.** Active board prices verified via DigiKey, Mouser, and manufacturer stores. Discontinued boards may be available through surplus, eBay, or university surplus channels.

---

## 6. Emerging Technologies

### SONOS (Silicon-Oxide-Nitride-Oxide-Silicon)

Microchip's PolarFire and PolarFire SoC use SONOS-based non-volatile configuration cells instead of traditional flash. SONOS offers:
- **Lower programming voltage** than flash
- **Better endurance** (100K+ cycles)
- **Smaller cell size** enabling higher density

### MRAM and FeRAM (Experimental)

Research devices use magnetic or ferroelectric non-volatile memory for FPGA configuration. Not commercially available in general-purpose programmable logic as of 2026.

---

## Further Reading

| Document | Source |
|---|---|
| Intel MAX 10 FPGA Device Overview | Intel (Doc 683658) |
| Lattice MachXO3 Family Data Sheet | Lattice Semiconductor |
| Microchip PolarFire FPGA Datasheet | Microchip |
| Microchip RTAX-S Radiation-Tolerant FPGAs | Microchip |
| Design Security in Nonvolatile Flash and Antifuse FPGAs | Microchip Whitepaper |
