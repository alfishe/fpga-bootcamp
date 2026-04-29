[← 06 Ip And Cores Home](../README.md) · [← Transceivers Home](README.md) · [← Project Home](../../../README.md)

# Transceiver Wizard & PHY IP Configuration

Configuring a modern FPGA transceiver means navigating the vendor's transceiver wizard — a GUI that generates the wrapper, clocking, and reset logic for your specific protocol. This article covers the common configuration options across Xilinx, Intel, and Lattice toolchains.

---

## Xilinx: Transceiver Wizard (7-Series / UltraScale+)

### CPLL vs QPLL Selection

| PLL Type | Frequency Range | Jitter | Max Line Rate | Notes |
|---|---|---|---|---|
| **CPLL (Channel PLL)** | 1.6–5.0 GHz (7S) / 3.3–6.6 GHz (US+) | Lower jitter | 12.5 Gbps (7S), 16.3 Gbps (US+) | Per-channel. Use for most protocols ≤ 12.5 Gbps. |
| **QPLL (Quad PLL)** | 5.9–12.5 GHz (7S) / 8.0–16.38 GHz (US+) | Higher jitter | Full line rate | Per-quad. Required for > 12.5 Gbps. Shared across 4 channels. |

**Rule of thumb:** CPLL for ≤ 10 Gbps (PCIe Gen1/2, SATA, 10GE with 64B/66B gearbox). QPLL for ≥ 12.5 Gbps (PCIe Gen3, 25GE).

### Clocking Topology

```
Refclk Pin (e.g., 156.25 MHz)
    │
    ▼
IBUFDS_GTE → CPLL/QPLL → TX PMA (line rate)
                        → RX CDR (line rate)
                        → TXOUTCLK / RXOUTCLK → BUFG_GT → fabric logic
```

### Common Configuration Options

| Option | Choices | Recommendation |
|---|---|---|
| **Encoding** | None / 8B10B / 64B66B / 64B67B | Match your protocol spec |
| **Data Width** | 16/20/32/40/64/80-bit | 32-bit for most. 64-bit for > 16 Gbps. |
| **TX Buffer** | Enabled / Bypass | Bypass if same refclk on both sides. Enable if RX has independent refclk. |
| **RX Buffer** | Enabled / Bypass | Enable for clock correction (ppm differences). |
| **Comma Alignment** | K28.5 (BC) / K28.1 (3C) / Custom | Standard: K28.5+. |
| **RX Equalization** | LPM / DFE | DFE for long reach (backplane), LPM for short (chip-to-chip). |

### Generated Wrapper Structure

```verilog
// Wizard generates:
my_gt_wrapper (
    // Clocks and resets
    .gt_refclk_p(), .gt_refclk_n(),
    .txusrclk_out(), .rxusrclk_out(),
    
    // TX parallel data interface
    .gt_txdata_i(32-bit parallel data),
    .gt_txcharisk_i(4-bit K-character flags),
    
    // RX parallel data interface
    .gt_rxdata_o(32-bit parallel data),
    .gt_rxcharisk_o(4-bit K-character flags),
    
    // Status
    .tx_resetdone_o(), .rx_resetdone_o(),
    .rx_cdr_locked_o(),    // CDR lock indicator
    
    // Serial pins
    .gt_txp_out(), .gt_txn_out(),
    .gt_rxp_in(), .gt_rxn_in()
);
```

---

## Intel: Transceiver PHY IP (Arria 10 / Stratix 10 / Agilex)

### PLL Selection

| PLL Type | Use Case |
|---|---|
| **ATX PLL** | Best jitter. Use for TX. Max ~17.4 Gbps (Arria 10). |
| **fPLL** | Lower frequency. Can drive both TX and RX. |
| **CDR PLL** | RX only. Built into each channel. |

### Key Configuration Differences from Xilinx

| Aspect | Xilinx | Intel |
|---|---|---|
| **Reset controller** | Wizard generates state machine | Manual or PHY IP helper |
| **Reconfiguration** | DRP (Dynamic Reconfiguration Port) | Avalon-MM reconfiguration interface |
| **Bonding** | TX phase alignment via dedicated clock routes | TX PLL cascading + bonding |
| **Pre-Emphasis** | Pre/post-cursor taps in GUI | VOD + Pre-emphasis in GUI |

---

## Lattice: DCU IP (ECP5)

The ECP5 DCU (Dynamic Clock Unit) is simpler than Xilinx/Intel transceivers:

- Max line rate: 3.2 Gbps
- Encoding: 8B/10B only
- PLL: per-quad, shared
- Configuration: Clarity Designer GUI (Radiant) or IPexpress (Diamond)

---

## Aurora Protocol Overview

Aurora is Xilinx's lightweight, open-standard, point-to-point serial protocol. It's the simplest way to get two FPGAs talking at multi-gigabit speeds.

| Feature | Aurora 8B/10B | Aurora 64B/66B |
|---|---|---|
| Encoding | 8B/10B | 64B/66B |
| Line rates | 0.5–13.1 Gbps | 10–25+ Gbps |
| Flow control | Native (NFC) or user | Native (NFC) or user |
| Channel bonding | Yes (up to 16 lanes) | Yes |
| Protocol overhead | ~2% (framing) | ~2% (framing) |

```
FPGA A                          FPGA B
┌──────────┐                   ┌──────────┐
│ Aurora IP│─── TX ───────────→│ Aurora IP│
│  (4-lane)│←── RX ────────────│  (4-lane)│
└──────────┘                   └──────────┘
   4 × 12.5 Gbps = 50 Gbps aggregate
```

**When to use Aurora vs PCIe:** Aurora for FPGA-to-FPGA (simpler, lower latency, no root complex). PCIe for FPGA-to-CPU (standard, driver support).

---

## IBERT — In-System Eye Scan

IBERT (Integrated Bit Error Ratio Test) is a built-in test pattern generator and checker that runs on the transceiver hardware without any user logic.

```
┌────── PRBS-31 Generator ──────┐
│   TX PMA → PCB trace → RX PMA  │
└────── PRBS-31 Checker ────────┘
         ↓
    BER counter (e.g., 10⁻¹⁵ → error-free)
    Eye diagram (2D bathtub curve)
```

**IBERT workflow:**
1. Instantiate IBERT core (Xilinx: IP Catalog → Debug → IBERT)
2. Connect to hardware via JTAG
3. Auto-scan: IBERT sweeps RX sampling point + CTLE/DFE settings
4. Read BER at each point → generates 2D eye diagram
5. Export optimal transceiver settings for production design

---

## Best Practices

1. **Run IBERT before writing a single line of protocol logic** — verifies the physical layer is solid
2. **Reset sequencing matters** — TX reset first, wait for `tx_resetdone`, then RX reset, wait for `rx_resetdone`, then wait for `cdr_locked`
3. **Don't ignore eye scan** — a closed eye at 8 Gbps due to poor PCB layout can't be fixed in RTL
4. **Quartus users: ATX PLL for TX, CDR for RX** — best jitter performance
5. **Monitor CDR lock in production** — if CDR unlocks, re-init the RX path

---

## References

- Xilinx PG168: 7 Series FPGAs Transceivers Wizard
- Xilinx PG182: UltraScale FPGAs Transceivers Wizard
- Xilinx PG246: IBERT for UltraScale+ GTY
- Intel AN 778: Using Transceiver Toolkit in Quartus Prime
- Lattice TN1278: ECP5 High-Speed I/O Interface
