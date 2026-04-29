[← FPGA-Only Home](README.md) · [← Cyclone V Home](../README.md) · [← Project Home](../../../../../README.md)

# Cyclone V Transceivers — GX & GT Variant Deep Dive

The GX and GT variants add multi-gigabit transceivers to the Cyclone V fabric. These are the same hardened transceiver blocks used across Intel's 28nm portfolio — shared with Arria V and Stratix V, scaled down in channel count and maximum line rate.

---

## Variant Transceiver Summary

| Variant | Channels | Max Line Rate | PCIe Hard IP | Protocol Support |
|---|---|---|---|---|
| **Cyclone V GX** | 4–8 | 3.125 Gbps | Gen2 ×1 | PCIe Gen1/2, GbE, CPRI, SerialLite, Basic |
| **Cyclone V GT** | 4–8 | 6.144 Gbps | Gen2 ×4 | PCIe Gen1/2, GbE, CPRI up to 6G, SerialLite, Basic |
| **Cyclone V E** | None | — | None | None |
| **Cyclone V SE/SX/ST** | 0 / 6×3.125G / 6×6.144G | — | Gen2 ×1/×4 | Same as GX/GT but in HPS domain |

> The transceiver silicon is **identical** between GX/GT (FPGA-only) and SX/ST (SoC) — same PMA, same PCS, same PHY IP. The difference is only in the hard IP blocks attached (PCIe controller, EMAC PCS).

---

## Transceiver Architecture

Each transceiver channel consists of:

```
┌─────────────────────────────────────────────┐
│  PMA (Physical Medium Attachment)           │
│  ┌──────────┐  ┌────────┐  ┌─────────────┐  │
│  │ TX PLL   │→ │ TX     │→ │ Serializer  │──┼── TX_p/TX_n
│  │ (LC PLL) │  │ Driver │  │ (8b/10b→bit)│  │
│  └──────────┘  └────────┘  └─────────────┘  │
│                                             │
│  ┌──────────┐  ┌────────┐  ┌─────────────┐  │
│  │ CDR      │← │ RX     │← │ Deserializer│──┼── RX_p/RX_n
│  │ (Clock   │  │ Buffer │  │ (bit→8b/10b)│  │
│  │ Recovery)│  └────────┘  └─────────────┘  │
│  └──────────┘                               │
├─────────────────────────────────────────────┤
│  PCS (Physical Coding Sublayer)             │
│  ┌────────────┐  ┌────────────┐             │
│  │ 8b/10b     │  │ Word       │             │
│  │ Enc/Dec    │  │ Aligner    │             │
│  └────────────┘  └────────────┘             │
│  ┌────────────┐  ┌────────────┐             │
│  │ Rate Match │  │ Byte Order │             │
│  │ FIFO       │  │ / Deskew   │             │
│  └────────────┘  └────────────┘             │
├─────────────────────────────────────────────┤
│  FPGA Fabric Interface                      │
│  ┌──────────────────────────┐               │
│  │ Native PHY IP (Quartus)  │← Parallel data│
│  │ or Transceiver PHY Reset │  at fabric clk│
│  │ Controller               │               │
│  └──────────────────────────┘               │
└─────────────────────────────────────────────┘
```

### PMA: Transmitter

| Parameter | GX | GT |
|---|---|---|
| **VCO range** | 1.25–3.125 GHz | 1.25–6.144 GHz |
| **Output swing** | 200–1600 mVpp (differential, programmable) | Same |
| **Pre-emphasis** | 2-tap (pre + post cursor) | Same |
| **Output impedance** | 100 Ω differential (nominal) | Same |
| **Rise/fall time** | < 60 ps (at max rate) | < 50 ps |

### PMA: Receiver

| Parameter | GX | GT |
|---|---|---|
| **CDR lock range** | ±200 ppm from reference | Same |
| **CTLE (Continuous Time Linear Equalizer)** | Fixed 4-stage | Same |
| **DFE (Decision Feedback Equalizer)** | 3-tap adaptive | 5-tap (GT) |
| **Input sensitivity** | < 50 mVpp differential | Same |
| **RX termination** | 100 Ω differential, on-die, programmable | Same |

### PCS Features

| Feature | Supported? | Notes |
|---|---|---|
| **8b/10b encoding** | Yes | Standard for PCIe Gen1/2, GbE, SerialLite |
| **Word aligner** | Yes | Comma detection (K28.5 for 8b/10b) |
| **Rate match FIFO** | Yes | ±300 ppm tolerance, delete/idle insertion |
| **Byte ordering / deskew** | Yes | Multi-lane alignment for PCIe ×4, XAUI |
| **RX bit slip** | Yes | Manual bit alignment for source-synchronous |
| **PRBS generator/checker** | Yes | PRBS-7, PRBS-15, PRBS-23, PRBS-31 for BER testing |
| **Loopback modes** | All | Serial, reverse serial, PCS parallel — critical for debug |
| **64b/66b encoding** | GT only | Required for 6G CPRI, higher-rate protocols |
| **TX PLL bandwidth** | Configurable | Low (clean eye) vs high (spread-spectrum tracking) |

---

## Clocking Architecture

Each transceiver bank (of 4 channels) has:

| Resource | Count per Bank | Notes |
|---|---|---|
| **TX PLL (LC PLL)** | 1 | Generates TX serial clock; shared by all 4 TX channels in bank |
| **CDR per channel** | 1 per RX | Independent clock recovery per RX lane |
| **Reference clock input** | 2 dedicated pins per bank | Differential or single-ended; 25–325 MHz |
| **FPGA fabric clock** | User-supplied | Parallel data width × line rate determines freq |

**Reference clock options:**
- Dedicated `REFCLK` pins per transceiver bank (recommended — lowest jitter)
- FPGA PLL output cascaded to transceiver REFCLK (higher jitter, flexible frequency)
- Internal calibration clock (for loopback testing only)

---

## Protocol Configuration Modes

### Basic (Custom PHY)

The most flexible mode. You define:
- Data width (8/10/16/20/32/40 bits)
- 8b/10b enabled/disabled
- Word alignment pattern
- Rate matching thresholds

Used for: proprietary serial links, ADC/DAC interfaces, custom framing protocols.

### PCI Express (PCIe)

| Feature | GX | GT |
|---|---|---|
| **Hard IP** | Gen2 ×1 | Gen2 ×4 |
| **LTSSM** | Hardware state machine | Hardware state machine |
| **BARs** | Up to 6× 32-bit BARs | Same |
| **MSI/MSI-X** | Supported | Supported |
| **Max payload size** | 256 bytes | 256 bytes |

The PCIe hard IP includes the full Physical Layer (PIPE interface), Data Link Layer, and Transaction Layer — no FPGA logic consumed for the protocol stack. Only the application layer (DMA engine, data path) is in fabric.

### GbE / SGMII

1.25 Gbps serial, 8b/10b encoded. The transceiver drives an RGMII/GMII interface to the FPGA fabric, where a soft or hard Ethernet MAC handles framing, CRC, and flow control. The HPS EMAC can also use an SGMII PHY via the FPGA transceiver.

### CPRI (Common Public Radio Interface)

Used in cellular base stations. Cyclone V GT supports CPRI line rates up to 6.144 Gbps (option 7). The 64b/66b PCS in GT is required for CPRI rates above 3.072 Gbps.

---

## Transceiver Channel Bonding

For multi-lane protocols (PCIe ×4, XAUI), channels must be bonded:

| Requirement | How |
|---|---|
| **Same TX PLL** | All bonded TX channels share one LC PLL — forces same data rate |
| **Same reference clock** | All bonded channels must use the same REFCLK source |
| **Skew control** | PCS deskew FIFOs align lanes to within 1 UI |
| **Channel placement** | Must be contiguous within a single transceiver bank |

> Channels 0–3 can be bonded; channels in different banks cannot. Plan your I/O placement early.

---

## Power & Thermal

| Parameter | Per Channel (GX) | Per Channel (GT) |
|---|---|---|
| **TX power** | ~100 mW at 3.125 Gbps | ~150 mW at 6.144 Gbps |
| **RX power** | ~120 mW | ~180 mW |
| **PCS power** | ~50 mW | ~80 mW |
| **Total per channel** | ~270 mW | ~410 mW |
| **4-channel bank total** | ~1.1 W | ~1.6 W |

Transceivers can easily be the dominant heat source on the die. For the GT variant with all 8 channels active at 6.144 Gbps, budget ~3.3 W for transceivers alone.

---

## Development Boards with Transceivers

| Board | Variant | Channels | Has PCIe? | Good For |
|---|---|---|---|---|
| **Cyclone V GX Starter Kit** | GX (5CGXFC5C6) | 6× 3.125G | Yes, ×1 edge | Transceiver bring-up, GbE, CPRI |
| **Cyclone V GT Dev Kit** | GT (5CGTFD9E5) | 8× 6.144G | Yes, ×4 edge | 6G serial, PCIe ×4, video broadcast |
| **SoCKit** | SX (5CSXFC6D6) | 6× 3.125G | Yes, ×4 | SoC + PCIe development |
| **DE10-Standard** | SX (5CSXFC6D6) | 6× 3.125G | No PCIe connector | SoC + transceiver learning |

---

## Best Practices

1. **Always use dedicated REFCLK pins** — FPGA PLL outputs have 10–50× the jitter of a clean external oscillator. For PCIe compliance (< 3 ps RMS jitter), a dedicated 100 MHz HCSL oscillator on REFCLK is mandatory.
2. **Reset the transceiver properly** — the Intel PHY Reset Controller IP handles the multi-cycle reset sequencing (TX PLL lock → TX reset → RX CDR lock → RX reset → word aligner reset). Never issue a single global reset to transceivers.
3. **Use PRBS for bring-up first** — before protocol debugging, verify the electrical link with PRBS-7 loopback (serial loopback first, then external loopback, then link partner).
4. **Plan channel bonding early** — moving bonded channels between banks requires redoing I/O planning.
5. **Monitor RX CDR lock status** — `rx_is_lockedtoref` and `rx_is_lockedtodata` signals tell you whether the CDR has lock. Log these during bring-up.

## Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **REFCLK jitter too high** | Intermittent link drops, high BER | Use dedicated oscillator, not FPGA PLL cascade |
| **Termination mismatch** | Eye diagram collapse, reflections | Ensure TX/RX termination matches PCB impedance (100 Ω diff) |
| **TX PLL not locked before TX enable** | No serial output, or garbage data | Wait for `pll_locked` assertion before deasserting TX reset |
| **Word aligner pattern wrong** | Never achieves word lock | Set comma pattern to match protocol standard (K28.5 = 0xBC for 8b/10b) |
| **Rate match FIFO overflow** | Periodic data corruption at RX | Tune delete/idle thresholds; check ±300 ppm compatibility |
| **Bonded channels in different banks** | Cannot bond — Quartus fitter error | Move all bonded channels to same bank, contiguous indices |

---

## References

| Source | Path |
|---|---|
| Cyclone V Device Handbook Vol. 2: Transceivers | Intel FPGA Documentation |
| Cyclone V GX/GT Transceiver PHY User Guide | Intel FPGA Documentation |
| Intel Transceiver PHY Reset Controller IP | Quartus IP Catalog |
| PCI Express Base Specification 2.0 | PCI-SIG |
| AN 753: Cyclone V GX Transceiver Characterization | Intel Application Note |
