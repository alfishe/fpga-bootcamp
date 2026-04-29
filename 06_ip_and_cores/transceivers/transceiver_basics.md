[← 06 Ip And Cores Home](../README.md) · [← Transceivers Home](README.md) · [← Project Home](../../../README.md)

# Multi-Gigabit Transceivers — PMA/PCS Architecture

Modern FPGA transceivers (GTP, GTH, GTY, GTM on Xilinx; GX, GT on Intel) are the physical-layer workhorses behind PCIe, 100G Ethernet, SATA, DisplayPort, JESD204B, and custom serial links. Understanding their internal PMA+PCS architecture is essential for any design above ~3 Gbps.

---

## PMA vs PCS: The Two Halves

```
┌────────────── PCS (Physical Coding Sublayer) ────────────────┐
│  FPGA Logic  │ 8B/10B │ Gearbox │ Elastic │ Comma  │   PMA   │
│  (Parallel)  │ 64B/66B│         │ Buffer  │ Detect │   I/F   │
└──────────────────────────────────────────────────────────────┘
                                                             │
┌────────────────────── PMA (Physical Medium Attachment) ────▼─────┐
│  Serializer  │  TX Driver  │  Channel  │  RX CDR  │ Deserializer │
│  (PISO)      │  (Pre-emph) │  (PCB)    │  (PLL)   │  (SIPO)      │
└──────────────────────────────────────────────────────────────────┘
```

| Layer | Function | Clock Domain |
|---|---|---|
| **PMA** | Analog: serialize/deserialize, TX driver, RX equalization, CDR (Clock Data Recovery) | Line rate (e.g., 10.3125 GHz) |
| **PCS** | Digital: encoding (8B/10B, 64B/66B), word alignment (comma detect), elastic buffering, gearbox | Parallel fabric rate (e.g., 322 MHz × 32-bit = 10.3 Gbps) |

---

## Transceiver Hierarchy by Vendor/Family

| Vendor | Low-End | Mid-Range | High-End | Max Line Rate |
|---|---|---|---|---|
| **Xilinx 7-Series** | GTP (Artix-7, Kintex-7, Zynq) | GTX (Kintex-7, Virtex-7) | GTH (Virtex-7) | 13.1 Gbps (GTH) |
| **Xilinx UltraScale+** | GTH (KU/K) | GTY (VU) | GTM (VU+) | 32.75 Gbps (GTM) |
| **Xilinx Versal** | GTY (Prime) | GTM (Premium) | — | 112 Gbps PAM4 (GTM) |
| **Intel Cyclone V** | GX (3–5 Gbps) | — | — | 3.125 Gbps |
| **Intel Arria 10** | GX (12.5 Gbps) | — | GT (17.4 Gbps) | 17.4 Gbps |
| **Intel Stratix 10** | GX (17.4 Gbps) | — | GX (28.3 Gbps) | 28.3 Gbps |
| **Intel Agilex 7** | F-Tile (32 Gbps) | — | E-Tile (58 Gbps PAM4) | 58 Gbps PAM4 |
| **Lattice ECP5** | DCU (3.2 Gbps) | — | — | 3.2 Gbps |
| **Lattice CertusPro-NX** | MIPI D-PHY + GbE | — | — | 10.3 Gbps (SGMII) |

---

## CDR (Clock Data Recovery) — The Heart of the PMA

The CDR extracts a clock from the incoming serial data stream without a forwarded clock:

1. **PLL locks** to the reference clock (e.g., 156.25 MHz for 10G)
2. **Phase detector** compares incoming data transitions with PLL phase
3. **Loop filter** averages phase error
4. **Phase interpolator** adjusts sampling point to data eye center
5. **CDR locks** → `rx_cdr_locked` asserts

**Critical design rule:** The reference clock frequency determines CDR lock range. If your refclk is off by > ±200 ppm (typical), CDR fails to lock.

---

## TX Equalization: Pre-Emphasis and De-Emphasis

At multi-gigabit rates, PCB traces act as low-pass filters. High-frequency components attenuate, closing the eye.

| Technique | How It Works | Parameter |
|---|---|---|
| **Pre-Emphasis** | Boost the first bit after a transition | Pre-cursor, post-cursor tap weights |
| **De-Emphasis** | Reduce non-transition bits (same effect) | C0/C1 in Xilinx TX driver |
| **TX Swing** | Adjust output voltage | 200–1200 mVppd (differential) |

```
Without EQ:     ___     ___          (eye closed)
               /   \___/   \___
              
With Pre-emph:  ___     ___         (eye open)
               /   \___/   \___
               └─boost─┘
```

---

## RX Equalization: CTLE + DFE

| Technique | Domain | How It Works | Config |
|---|---|---|---|
| **CTLE (Continuous Time Linear Equalizer)** | Analog | High-pass filter that amplifies attenuated high frequencies | Gain boost: 0–16 dB |
| **DFE (Decision Feedback Equalizer)** | Digital | Cancels post-cursor ISI using previously detected bits | Number of taps: 1–16 |

**Modern transceivers use adaptive DFE** — the RX automatically tunes tap coefficients to open the eye. Manually tuning CTLE/DFE is increasingly rare (required mainly for backplane/long-reach links).

---

## PCS Encoding: 8B/10B vs 64B/66B

| Encoding | Overhead | DC Balance | When to Use | Max Rate (Typical) |
|---|---|---|---|---|
| **8B/10B** | 25% | Yes (running disparity) | ≤ 10 Gbps. Legacy friendly, simple. | ~10 Gbps |
| **64B/66B** | 3.125% | Scrambler-based | > 10 Gbps. PCIe Gen3+, 100G Ethernet. | 100+ Gbps |
| **128B/130B** | 1.56% | Scrambler-based | PCIe Gen3/4/5. 256B/257B for 400G Ethernet. | 400+ Gbps |
| **PAM4 (RS-FEC)** | Varies | FEC-based | 50+ Gbps per lane. Versal GTM, Agilex E-Tile. | 112 Gbps PAM4 |

**8B/10B key benefit:** Guaranteed transition density (never more than 5 consecutive identical bits) — makes CDR easy. 64B/66B relies on a scrambler for transition density and FEC for error correction.

---

## Comma Detection and Word Alignment

In 8B/10B mode, the transceiver searches for a **comma character** (K28.5 = 0xBC or K28.1 = 0x3C) to establish word boundaries:

```
Serial stream: …0101111100 0011111010 1100000101…
                          ↑ comma (K28.5)
                          → byte alignment point
```

**64B/66B:** Uses sync header bits (01 = data, 10 = control) to frame 66-bit blocks. No comma needed.

---

## Reference Clock Requirements

| Protocol | Line Rate | Refclk Options | Jitter Requirement |
|---|---|---|---|
| **PCIe Gen2 (5 GT/s)** | 5.0 Gbps | 100 MHz (HCSL) | < 3 ps RMS (12 kHz–20 MHz) |
| **PCIe Gen3 (8 GT/s)** | 8.0 Gbps | 100 MHz | < 1 ps RMS |
| **PCIe Gen4 (16 GT/s)** | 16.0 Gbps | 100 MHz | < 0.5 ps RMS |
| **10G Ethernet** | 10.3125 Gbps | 156.25 MHz or 322.265625 MHz | < 0.7 ps RMS |
| **25G Ethernet** | 25.78125 Gbps | 156.25 MHz | < 0.3 ps RMS |

**Golden rule:** Use a dedicated, low-jitter oscillator for transceiver reference clocks. Never drive a transceiver refclk from FPGA-generated (PLL-derived) clocks — the jitter accumulation makes CDR unreliable.

---

## Best Practices

1. **Run IBERT (Integrated Bit Error Ratio Test)** before deploying any transceiver design — verifies physical link integrity
2. **AC-coupling capacitors:** 100 nF for ≤ 12.5 Gbps, 220 nF for > 12.5 Gbps. Place within 5 mm of receiver.
3. **Reference clock sharing:** One quad can share one refclk. Different protocols (PCIe + 10GE) in same quad → separate refclks or use CPLL for one.
4. **Never route transceiver refclk through FPGA fabric** — use dedicated refclk pins with direct PMA connection
5. **Termination:** Transceivers are internally 100 Ω differential terminated. No external termination resistors needed.

---

## References

- Xilinx UG476: 7 Series FPGAs GTX/GTH Transceivers
- Xilinx UG578: UltraScale Architecture GTY Transceivers
- Intel AN 794: Transceiver PHY IP Core
- Lattice TN1278: ECP5 High-Speed I/O Interface
