[← Home](../../README.md) · [Architecture](../README.md) · [Infrastructure](README.md)

# IO Standards & SERDES — Talking to the Outside World

Your FPGA is useless if it can't communicate. The IO bank — a group of pins sharing a common voltage reference and driver architecture — determines what signaling standards your design can use and at what speed. This article covers the IO standards and SERDES (Serializer/Deserializer) architectures across all major FPGA vendors, from simple 3.3V LVCMOS to 58 Gbps PAM4 transceivers.

---

## Overview

FPGA IO architecture is organized into **banks** — groups of pins (typically 24–52) that share a common supply voltage (VCCO) and reference voltage (VREF). Every bank supports a specific set of IO standards: single-ended (LVCMOS, LVTTL, SSTL, HSTL) and differential (LVDS, LVPECL, HCSL, TMDS). Above ~1 Gbps, general-purpose IO pins give way to dedicated **multi-gigabit transceivers (MGTs)** — hardened SERDES blocks with PMA (Physical Medium Attachment: analog front-end, CDR, equalization) and PCS (Physical Coding Sublayer: 8b/10b, 64b/66b encoding). Understanding bank architecture is the prerequisite for pin planning; ignoring it leads to impossible pinouts and PCB respins.

---

## IO Bank Architecture

```
┌─────── IO Bank (Xilinx: HP/HR/HD) ───────┐
│  VCCO = 1.2V–3.3V (supply rail)          │
│  VREF = VCCO/2 (for SSTL/HSTL)           │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐         │
│  │Pin 0│ │Pin 1│ │Pin 2│ │...  │ (24–52) │
│  └─────┘ └─────┘ └─────┘ └─────┘         │
│     All share same VCCO, IO standard     │
│     Differential pairs: N+1 paired       │
│     Clock-capable: subset of pins        │
└──────────────────────────────────────────┘
```

> [!WARNING]
> **One VCCO per bank.** You cannot have 1.8V LVCMOS and 2.5V LVCMOS in the same bank. A single bank = single voltage standard for all single-ended signals. Plan your pinout accordingly.

### Bank Types (Xilinx)

| Bank Type | VCCO Range | Supported Standards | Max Rate | Use |
|---|---|---|---|---|
| **HR (High Range)** | 1.2V–3.3V | LVCMOS, LVTTL, SSTL, HSTL, LVDS_25 | 1.25 Gbps | General IO, legacy standards |
| **HP (High Performance)** | 1.0V–1.8V | LVDS, SSTL, HSTL, POD (DDR4) | 1.6 Gbps | High-speed, DDR3/DDR4 memory |
| **HD (High Density)** | 1.2V–3.3V | Like HR but no differential termination | 800 Mbps | UltraScale+ only, low-power general IO |

### Bank Types (Intel)

| Bank Type | VCCO Range | Supported Standards | Max Rate |
|---|---|---|---|
| **3.3V IO** | 1.2V–3.3V | LVCMOS, LVTTL, SSTL-2/3/18/15, HSTL | 1.2 Gbps |
| **1.8V IO** | 1.2V–1.8V | LVDS, SSTL-135/15, HSTL-15, POD | 1.6 Gbps |

---

## IO Standards Reference

### Single-Ended Standards

| Standard | VCCO | VOH/VOL (approx) | Max Rate | Use Case |
|---|---|---|---|---|
| **LVCMOS33** | 3.3V | 3.3V / 0V | 200 MHz | Legacy, slow peripherals |
| **LVCMOS25** | 2.5V | 2.5V / 0V | 250 MHz | Legacy |
| **LVCMOS18** | 1.8V | 1.8V / 0V | 350 MHz | Modern peripherals |
| **LVCMOS15** | 1.5V | 1.5V / 0V | 400 MHz | DDR2, newer interfaces |
| **LVCMOS12** | 1.2V | 1.2V / 0V | 500 MHz | DDR4, ultra-low-power |
| **SSTL18 (DDR3)** | 1.8V | VCCO/2 ± 400 mV | 800 Mbps | DDR3 SDRAM |
| **SSTL15 (DDR3L)** | 1.5V | VCCO/2 ± 350 mV | 800 Mbps | DDR3L SDRAM |
| **POD12 (DDR4)** | 1.2V | VCCO-terminated | 1.6 Gbps | DDR4 SDRAM |
| **HSTL18** | 1.8V | VCCO/2 ± 500 mV | 400 MHz | High-speed memory interfaces |

### Differential Standards

| Standard | VOD (swing) | Common Mode | Max Rate | Use Case |
|---|---|---|---|---|
| **LVDS** | 350 mV | 1.2V | 1.6 Gbps (general), 2.5 Gbps (HP) | General high-speed, FPD-Link |
| **LVPECL** | 800 mV | 2.0V | 3+ Gbps | High-speed clock distribution |
| **HCSL** | 700 mV | 350 mV | 400 MHz | PCIe reference clock |
| **TMDS** | 500 mV | 3.0V (AVcc) | 3.4 Gbps (per channel) | HDMI/DVI |
| **SLVS-400 (MIPI D-PHY)** | 200 mV | 200 mV | 1.5 Gbps | MIPI camera/display |
| **CML** | 400 mV | VCCO-0.2V | 12+ Gbps | Multi-gigabit SERDES |

---

## Multi-Gigabit Transceivers (SERDES)

For data rates above ~1.6 Gbps, general-purpose IO pins are replaced by dedicated transceiver quads — PMA + PCS blocks with analog CDR (Clock and Data Recovery), equalization, and serialization.

### Vendor Transceiver Comparison

| Feature | Xilinx GTY | Xilinx GTM | Intel E-tile | Lattice SERDES (ECP5) | Microchip XCVR (PolarFire) |
|---|---|---|---|---|---|
| **Max line rate** | 32.75 Gbps | 58 Gbps (PAM4) | 58 Gbps (PAM4) | 5 Gbps | 12.7 Gbps |
| **Modulation** | NRZ | NRZ/PAM4 | NRZ/PAM4 | NRZ | NRZ |
| **CDR range** | ±200 ppm | ±200 ppm | ±200 ppm | ±200 ppm | ±200 ppm |
| **Equalization** | CTLE + DFE (5-tap) | CTLE + DFE (15-tap) | CTLE + DFE (7-tap) | CTLE only | CTLE + DFE (5-tap) |
| **PCS encoding** | 8b/10b, 64b/66b, 64b/67b | Same + RS-FEC | Same + RS-FEC | 8b/10b | 8b/10b, 64b/66b |
| **Protocol hard IP** | PCIe Gen1–4, SATA, XAUI, CPRI, JESD204B/C | PCIe Gen5, 100G/400G Ethernet | PCIe Gen1–4, 100G/200G Ethernet | PCIe Gen2 (some) | PCIe Gen2 |
| **Phase interpolator** | Yes (per channel) | Yes (per channel) | Yes (per channel) | No | Yes |

### Transceiver Architecture

```
┌────────── Transceiver Channel ─────────────────────┐
│  TX Path:                                          │
│  FPGA → PCS (encoder) → PMA (serializer)           | 
│            → TX Driver (pre-emphasis) → Pad        |
│                                                    │
│  RX Path:                                          │
│  Pad → CTLE (equalizer) → CDR → DFE                │
│       → PMA (deserializer) → PCS (decoder) → FPGA  |
│                                                    │
│  Reference Clock: dedicated refclk pin             │
│  Loop BW, charge pump, VCO: tunable                │
└────────────────────────────────────────────────────┘
```

**Equalization:** High-speed serial signals degrade over PCB traces. The receiver's **CTLE (Continuous-Time Linear Equalizer)** amplifies high-frequency components; **DFE (Decision Feedback Equalizer)** cancels post-cursor ISI using feedback from previous bit decisions.

---

## Pin Planning Constraints

### Bank Voltage Rules

1. All single-ended signals in a bank must use the same VCCO
2. Differential signals (LVDS, LVPECL) typically require specific VCCO for termination
3. Input-only pins can accept standards above VCCO (with external termination)
4. Clock-capable pins (MRCC, SRCC) are bank-specific — each bank has a limited number

### Simultaneous Switching Output (SSO) Limits

| Parameter | Rule of Thumb |
|---|---|
| SSO per bank | 50–70% of pins can switch simultaneously |
| SSO per power pair (VCCIO/GND) | 8:1 signal-to-return ratio for LVCMOS |
| SSO per device | Limited by total ground bounce budget |

Exceeding SSO limits causes ground bounce — the internal ground reference shifts during switching, causing false logic transitions on quiet pins.

---

## When to Use / When NOT to Use

### When to Use Each Standard

| Standard | Ideal Scenario |
|---|---|
| **LVCMOS33/25** | Legacy peripherals, slow SPI/I2C/UART, push-button/reset input |
| **LVCMOS18/15/12** | Modern peripherals (SPI flash, sensors), DDR3/4 address/command |
| **LVDS** | General high-speed (ADC/DAC data, camera links), any differential interface up to 1.6 Gbps |
| **SSTL/POD** | DDR3/DDR4 memory interfaces exclusively. Not for general IO |
| **MGT (GTP/GTX/GTY/GTM)** | PCIe, 10G/25G/100G Ethernet, JESD204B, CPRI, SATA, DisplayPort, HDMI 2.1 |
| **TMDS** | HDMI/DVI (use vendor IP or dedicated TMDS drivers) |

### When NOT to Use

| Mistake | Recommendation |
|---|---|
| Using LVDS for a 10 MHz SPI clock | Overkill. LVCMOS33 at 10 MHz works fine. LVDS adds common-mode and termination complexity |
| Using SSTL for a GPIO LED | SSTL requires VREF and termination. LVCMOS33 is simpler and works identically at low speed |
| Connecting 3.3V peripheral to 1.8V HP bank | HR bank needed for >1.8V. Use voltage level translator if no HR bank is available → see [IO Voltage Levels & Level Translation](../../09_board_design/io_voltage_levels.md) |
| Routing a 10G MGT through general IO | Impossible. MGTs have dedicated analog pins and quad locations |

---

## Best Practices & Antipatterns

### Best Practices
1. **Group signals by VCCO** — All 1.8V signals in one bank, all 3.3V in another. This maximizes usable pin count
2. **Pair differential pins correctly** — `_P` and `_N` must be in adjacent pins within the same bank. Xilinx: `N` number and `N+1`
3. **Don't use DCI (Digitally Controlled Impedance) unless needed** — DCI uses internal calibration resistors that consume IO bank resources and power. External termination is more predictable
4. **Verify SSO budget** — Use vendor power estimator to check SSO limits before freezing pinout

### Antipatterns

| Antipattern | The Problem | The Fix |
|---|---|---|
| **"The Mixed-Voltage Bank"** | Placing a 2.5V UART TX and 1.8V SPI in the same bank | VCCO can only be one voltage. Separate into different banks |
| **"The Transceiver Shortcut"** | Routing a GTY refclk through a general-purpose clock input "because it's nearby" | GTY refclks have specific, dedicated pins with ultra-low-jitter paths. General clock pins add 3–5× more jitter |
| **"The TERMless DDR"** | DDR3 interface without ODT (On-Die Termination) or external VTT termination | Reflections on the data bus cause eye closure. DDR3/DDR4 require termination per JEDEC spec |
| **"The Unreferenced VREF"** | Enabling SSTL/HSTL but not connecting VREF pins for the bank | SSTL/HSTL receivers compare the signal to VREF. Without correct VREF, the input threshold floats |

---

## Pitfalls & Common Mistakes

### 1. Bank VCCO Mismatch on Differential Inputs

**The mistake:** LVDS receiver on a 3.3V VCCO bank. The LVDS common-mode is 1.2V.

**Why it fails:** LVDS receivers on HR banks require VCCO = 2.5V for proper common-mode bias. A 3.3V VCCO shifts the receiver's operating point, degrading input sensitivity.

**The fix:** Place LVDS receivers on banks with VCCO = 2.5V (HR) or 1.8V (HP). Check the device datasheet for differential receiver VCCO requirements.

### 2. Transceiver Reference Clock Jitter

**The mistake:** Using a 50 ppm, 5 ps RMS jitter oscillator for a 10G Ethernet reference clock.

**Why it fails:** 10GBASE-R (10.3125 Gbps) requires <1 ps RMS jitter on the reference. 5 ps jitter causes excessive TX eye closure, failing compliance at the receiver.

**The fix:** Use a <500 fs RMS jitter reference (e.g., Si5345, LMK04828). Dedicated transceiver refclks have their own low-jitter PLL; do not share fabric PLLs for transceiver refclks.

---

## References

| Source | Document |
|---|---|
| Xilinx UG471 — 7-Series SelectIO | https://docs.xilinx.com/ |
| Xilinx UG476 — 7-Series GTX/GTH Transceivers | https://docs.xilinx.com/ |
| Xilinx UG581 — UltraScale GTM Transceivers | https://docs.xilinx.com/ |
| Intel CV-5V2 — Cyclone V IO and Transceivers | Intel FPGA Documentation |
| Lattice TN1262 — ECP5 sysIO Usage Guide | Lattice Tech Docs |
| [Clocking—PLL, MMCM, DCM](clocking.md) | Previous article — clock generation |
| [Configuration & Bitstream](configuration.md) | Next article |
