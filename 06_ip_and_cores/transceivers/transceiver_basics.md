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

## Link Training & Auto-Negotiation

For protocol-aware links (PCIe, Ethernet), transceivers must negotiate speed and width:

| Protocol | Link Training | Auto-Negotiation | Speed Upgrade |
|---|---|---|---|
| **PCIe Gen1/2** | TS1/TS2 ordered sets | Gen1 only (2.5 GT/s), then uptrain | Gen1 → Gen2 via Recovery |
| **PCIe Gen3/4** | TS1/TS2 + 8GT/s EQ | Gen1 (2.5 GT/s), then Recovery to Gen3/4 | Requires TX/RX equalization handshake |
| **10GBASE-KR** | AN/LT (Auto-Neg + Link Training) | KR-specific AN frame exchange | Not applicable (fixed 10.3125 Gbps) |
| **CEI-25G** | Continuous time adaptation | No AN; fixed rate | N/A |

### PCIe Equalization (Gen3/4/5)
PCIe Gen3+ requires transmitter preset and receiver preset coordination:
1. Link starts at Gen1 (2.5 GT/s)
2. Transitions to Gen3 (8 GT/s) via Recovery
3. **Phase 1:** TX sends preset values (P0–P10); RX evaluates eye
4. **Phase 2:** RX requests preset/coefficient adjustments via TS1
5. **Phase 3:** TX applies final coefficients; link enters L0

If equalization fails, the link falls back to Gen2 (5 GT/s) or Gen1.

---

## Redriver vs Retimer: PCB Design Decisions

When a high-speed link must traverse a long PCB trace or a cable, signal integrity degrades:

| Component | Function | Latency | When to Use | Cost |
|---|---|---|---|---|
| **Redriver** | Analog amplification + EQ | ~0 ps (analog) | Short reach extension (<1m total), simple traces | $1–$5 |
| **Retimer** | Full CDR + retransmit | ~20–40 ns (digital) | Long reach (>1m), cables, backplanes | $10–$30 |
| **Direct connect** | None | 0 | Standard PCB trace <6 inches | $0 |

**Rule of thumb for FPGA transceivers:**
- PCIe Gen2/3 on same PCB: direct connect (no redriver)
- PCIe Gen4 on same PCB: redriver if trace >8 inches
- PCIe over cable: retimer required
- 25G Ethernet on same PCB: direct connect if trace <6 inches

---

## Transceiver Quad Architecture

FPGA transceivers are organized in quads (groups of 4 channels sharing resources):

```
┌──────────── Quad ────────────┐
│  CH0  CH1  CH2  CH3           │
│  GT→  GT→  GT→  GT→           │
│  ┌─────────────┐             │
│  │  QPLL / CPLL │  Shared PLL│
│  └─────────────┘             │
│  ┌─────────────┐             │
│  │  REFCLK pins │  Shared ref│
│  └─────────────┘             │
└──────────────────────────────┘
```

| Shared Resource | Constraint |
|---|---|
| **QPLL (Quad PLL)** | All channels in the quad must run at the same line rate or integer multiples |
| **CPLL (Channel PLL)** | Per-channel PLL allows independent line rates within a quad |
| **Reference clock** | One refclk pair feeds all 4 channels; different rates require separate refclks |
| **Power rails** | MGTAVCC, MGTAVTT, MGTVCCAUX are shared per quad |

**Pitfall:** If you place two protocols with incompatible line rates (e.g., PCIe Gen3 at 8 GT/s and 10GbE at 10.3125 Gbps) in the same quad, they cannot share the QPLL. Use CPLL for one or place them in different quads.

---

## Debugging Transceiver Links

| Symptom | Likely Cause | Debug Step |
|---|---|---|
| **CDR never locks** | Bad refclk (jitter/freq) | Probe refclk with spectrum analyzer; verify ppm accuracy |
| **High BER after link up** | Insufficient TX pre-emphasis | Run IBERT eye scan; adjust TX pre-cursor/post-cursor |
| **Link drops intermittently** | Power supply noise on MGTAVCC | Scope MGTAVCC during traffic burst; add decoupling |
| **No comma detect** | Polarity inversion | Check `RXPOLARITY` pin; swap P/N PCB traces or set polarity bit |
| **Elastic buffer overflow/underflow** | Clock frequency mismatch | Verify rate match FIFO settings; check refclk ppm tolerance |
| **Link works on one board but not another** | PCB length mismatch | Run TDR on both boards; compare eye diagrams at receiver |

---

## Best Practices

1. **Run IBERT (Integrated Bit Error Ratio Test)** before deploying any transceiver design — verifies physical link integrity
2. **AC-coupling capacitors:** 100 nF for ≤ 12.5 Gbps, 220 nF for > 12.5 Gbps. Place within 5 mm of receiver.
3. **Reference clock sharing:** One quad can share one refclk. Different protocols (PCIe + 10GE) in same quad → separate refclks or use CPLL for one.
4. **Never route transceiver refclk through FPGA fabric** — use dedicated refclk pins with direct PMA connection
5. **Termination:** Transceivers are internally 100 Ω differential terminated. No external termination resistors needed.
6. **Place protocols with the same line rate in the same quad** — saves QPLL resources and simplifies clocking
7. **Always probe MGT power rails during traffic** — transceivers draw burst current; insufficient decoupling causes CDR unlocks

---

## Cross-References

| Topic | Article |
|---|---|
| Transceiver IP configuration | [Transceiver IP](transceiver_ip.md) |
| PCIe link training debug | [PCIe Bringup](../../15_case_studies/pcie_bringup.md) |
| High-speed PCB design | [Section 09 — Board & PCB Design](../../09_board_and_pcb_design/README.md) |
| Clock network design | [Clock Network Design](../../02_architecture/infrastructure/clock_network_design.md) |

---

## References

- Xilinx UG476: 7 Series FPGAs GTX/GTH Transceivers
- Xilinx UG578: UltraScale Architecture GTY Transceivers
- Intel AN 794: Transceiver PHY IP Core
- Lattice TN1278: ECP5 High-Speed I/O Interface
- PCIe Base Specification Rev 4.0 (equalization protocol)
- IBERT User Guide (Xilinx PG245)
