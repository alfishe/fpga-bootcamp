[← 06 Ip And Cores Home](../README.md) · [← Other Hard Ip Home](README.md) · [← Project Home](../../../README.md)

# Hard Ethernet MACs — Vendor IP Comparison and Integration Patterns

Most modern FPGAs include hardened Ethernet MAC (Media Access Controller) blocks that handle the MAC-layer framing, pause frame processing, statistics collection, and PCS (Physical Coding Sublayer) interface — eliminating the need for soft-MAC implementations for standard Ethernet rates. This article compares the hard MAC offerings across vendors and provides integration patterns for common use cases.

> [!NOTE]
> For high-speed serial transceivers (SerDes, PMA) that sit below the MAC, see [Transceiver Basics](../transceivers/transceiver_basics.md). For networking cores (open-source Ethernet stacks), see [Ethernet Cores](../../12_open_source_open_hardware/networking/ethernet_cores.md).

---

## Why Hard MAC Matters

| Metric | Soft MAC (RTL) | Hard MAC (Silicon) |
|---|---|---|
| LUT utilization | 2,000–8,000 LUTs (10G) | 0 LUTs |
| Latency | Variable | Fixed, deterministic |
| Power | 1–3 W (dynamic fabric) | <0.5 W (hardened) |
| Features | Whatever you implement | Vendor-defined (less flexible) |
| Multi-port | Scales linearly in LUTs | Limited by hard block count |
| Certification | Must self-certify | Pre-certified by vendor |

**Decision rule:** Use hard MAC for standard protocols (1G/10G/25G/100G). Use soft MAC only for custom/proprietary MAC-layer protocols or when no hard MAC is available on your device.

---

## Protocol Stack: Where the MAC Sits

```
┌─────────────────────────────┐
│  User Logic (AXI4-Stream)   │ ← Your packet processing
├─────────────────────────────┤
│  MAC (Hard or Soft)         │ ← Framing, address filtering, pause, stats
├─────────────────────────────┤
│  PCS (64B/66B or 8B/10B)    │ ← Encoding + scrambling
├─────────────────────────────┤
│  PMA (SerDes)               │ ← Serialization
└─────────────────────────────┘
        │
    ────▼────
    RJ45 / SFP / QSFP
```

The MAC is responsible for:
- **Transmit:** Adding preamble, Start-of-Frame Delimiter (SFD), padding, FCS (Frame Check Sequence)
- **Receive:** Stripping preamble/SFD, FCS verification, address filtering (promiscuous/unicast/multicast)
- **Flow control:** IEEE 802.3x pause frame generation and processing
- **Statistics:** TX/RX frame counters, error counters, oversize/undersize counters

---

## Vendor Hard MAC Comparison

### Xilinx

| IP Block | Rates | Interfaces | Families | Notes |
|---|---|---|---|---|
| **TEMAC (Tri-Mode)** | 10/100/1000 Mbps + 2.5G | GMII, RGMII, SGMII | 7-Series, UltraScale+ | Most common 1G hard MAC. Tri-mode = auto-negotiation built-in. |
| **XXVEMAC** | 10G/25G | AXI4-Stream, 25G CAUI-4 | UltraScale+, Versal | Hard 10/25G MAC+PCS. 64B/66B PCS included. |
| **USXGMII** | 10M/100M/1G/2.5G/5G/10G | USXGMII (Cisco SGMII extension) | UltraScale+ GTH/GTY | Single serial link for multi-rate. Used in enterprise switches. |
| **MRMAC (Multi-Rate)** | 10G/25G/40G/50G/100G | Flexible AXI4-Stream, CAUI-4, RS-FEC | Versal Premium | Most flexible. Software-reconfigurable between rates. |
| **CMAC** | 100G | CAUI-4 (4×25G), CAUI-10 (10×10G) | UltraScale+ VU9P+ | Hardened 100G MAC with RS-FEC (528,514). |

### Intel (Altera)

| IP Block | Rates | Interfaces | Families | Notes |
|---|---|---|---|---|
| **HPS EMAC** | 10/100/1000 Mbps | RGMII/GMII (HPS-side) | Cyclone V SoC, Arria 10 SoC | Integrated into HPS. Provides Linux eth0. |
| **Triple-Speed Ethernet** | 10/100/1000 Mbps | GMII, RGMII, SGMII | All families (soft) or hard in HPS | HPS variant is hard; fabric variant is soft. |
| **E-Tile Ethernet** | 10G/25G/100G | AXI4-Stream, CAUI-4 | Stratix 10, Agilex 7 | Hard MAC+PCS+FEC. Native 25G RS-FEC. |
| **F-Tile Ethernet** | 10G/25G/50G | AXI4-Stream, CAUI-4 | Agilex 7 | Lower power than E-Tile. For mid-range designs. |

### Lattice

| IP Block | Rates | Interfaces | Families | Notes |
|---|---|---|---|---|
| **GigE MAC** | 10/100/1000 Mbps | GMII, RGMII, SGMII | ECP5, CertusPro-NX | Soft IP only. ~2K LUTs. |
| **SGMII/GbE PCS** | 1.25 Gbps (SGMII) | Serial (DCU) | ECP5 (with DCU) | Hard PCS in serdes. Soft MAC on top. |

### Microchip

| IP Block | Rates | Interfaces | Families | Notes |
|---|---|---|---|---|
| **10/100/1000 MAC** | 1G | GMII, RGMII | PolarFire, SmartFusion2 | Soft MAC. ~1.5K LUTs. Good enough for 1G. |
| **XAUI MAC** | 10G | XAUI (4×3.125G) | PolarFire | Hard XAUI PCS + soft MAC. |

---

## Xilinx TEMAC Instantiation Example

```verilog
// Xilinx Tri-Mode Ethernet MAC (TEMAC) instantiation
// 7-Series / UltraScale+ — Vivado 2023.2
// Uses RGMII interface to external PHY

temac_gbe_wrapper u_temac (
    // Clock and reset
    .glbl_rstn       (rst_n),
    .rx_axi_rstn     (rx_rst_n),
    .tx_axi_rstn     (tx_rst_n),

    // RX AXI4-Stream (MAC → User)
    .rx_axis_tdata   (rx_tdata),
    .rx_axis_tvalid  (rx_tvalid),
    .rx_axis_tlast   (rx_tlast),
    .rx_axis_tuser   (rx_tuser),     // Error indicator

    // TX AXI4-Stream (User → MAC)
    .tx_axis_tdata   (tx_tdata),
    .tx_axis_tvalid  (tx_tvalid),
    .tx_axis_tlast   (tx_tlast),
    .tx_axis_tuser   (tx_tuser),     // 0=normal, 1=error
    .tx_axis_tready  (tx_tready),

    // RGMII PHY interface
    .rgmii_txd       (rgmii_txd),    // TX data to PHY
    .rgmii_tx_ctl    (rgmii_tx_en),
    .rgmii_txc       (rgmii_txc),    // TX clock to PHY
    .rgmii_rxd       (rgmii_rxd),    // RX data from PHY
    .rgmii_rx_ctl    (rgmii_rx_dv),
    .rgmii_rxc       (rgmii_rxc),    // RX clock from PHY

    // MDIO management
    .mdio_mdio       (mdio_data),
    .mdio_mdc        (mdio_clk),

    // Status
    .phy_addr        (5'h01),        // PHY address for MDIO
    .speed_is_100b   (speed_100),
    .speed_is_10b    (speed_10)
);
```

---

## When to Use Which

| Scenario | Recommended IP | Why |
|---|---|---|
| Embedded Linux on SoC (Zynq/Cyclone V SoC) | HPS/GEM EMAC | Already there, use it — Linux driver built-in |
| 1G copper (RJ45) on FPGA-only chip | TEMAC or Triple-Speed Ethernet + external PHY | Hard MAC + RGMII PHY is simplest |
| 10G SFP+ optical | XXVEMAC (Xilinx) or E-Tile (Intel) | Hard MAC + 64B/66B PCS |
| 25G SFP28 | XXVEMAC (Xilinx) or F-Tile (Intel) | Hard MAC with RS-FEC |
| 100G QSFP28 | CMAC (Xilinx US+) or E-Tile (Intel S10/Agilex) | Hard 100G with RS-FEC |
| Custom/proprietary MAC protocol | Soft MAC | Full control over framing |
| Multi-rate enterprise switch | USXGMII (Xilinx) or MRMAC (Versal) | Software-selectable rate |
| Lattice ECP5 with 1G | GigE MAC (soft) + external PHY | No hard MAC available |
| Microchip PolarFire 10G | XAUI MAC + 4-lane XAUI PHY | Hard PCS + soft MAC |

---

## Best Practices

1. **Use hard MAC whenever available** — soft MAC costs 2K–8K LUTs and cannot match the deterministic latency of hardened silicon
2. **Connect via AXI4-Stream** — all modern vendor MAC IP uses AXI4-Stream for data; this lets you insert your processing pipeline between MAC and application without bus-width conversion
3. **Enable statistics counters** — all hard MACs include MIB-style counters (TX/RX frames, errors, undersize, oversize); expose these via AXI4-Lite for runtime monitoring
4. **Use MDIO for PHY management** — configure link speed, auto-negotiation, and loopback via MDIO; don't hardwire PHY straps unless pin-constrained
5. **Pause frame handling** — enable IEEE 802.3x pause on the MAC when your downstream processing may backpressure; this prevents dropped frames during traffic bursts

---

## Pitfalls

### 1. RGMII Requires DDR I/O and Clock Delay
RGMII uses double-data-rate signaling (2 bits per clock edge). The FPGA I/O must be configured for DDR mode. Additionally, the RGMII specification requires a 2 ns clock delay (or PCB trace delay) at the receiver.

**Fix:** Use Xilinx IODELAYE1/IDELAYE2 or Intel I/O DDR registers with programmable delay. Set the delay to approximately 2 ns at the PHY side.

### 2. FCS Verification is Optional on Some Soft MACs
If you implement a soft MAC, you may forget to verify the Frame Check Sequence (FCS/CRC-32). This causes silent data corruption.

**Fix:** Always enable FCS verification in the MAC. For soft MACs, implement a CRC-32 checker on RX and a CRC-32 generator on TX.

### 3. AXI4-Stream Width Mismatch Between MAC and Your Logic
Xilinx XXVEMAC uses 64-bit AXI4-Stream at 156.25 MHz for 10G. If your processing pipeline operates at a different width or clock, you need a width converter and possibly a clock-domain crossing FIFO.

**Fix:** Match your pipeline width to the MAC's native AXI4-Stream width, or insert an AXI4-Stream Data FIFO with independent clock domains.

---

## References

- Xilinx PG051: Tri-Mode Ethernet MAC LogiCORE IP
- Xilinx PG318: USXGMII Subsystem
- Xilinx PG203: UltraScale+ 100G Ethernet (CMAC)
- Xilinx PG210: XXVEMAC
- Intel AN 647: Triple-Speed Ethernet IP Core
- Intel UG-20051: E-Tile Ethernet IP User Guide
- Lattice TN1278: ECP5 High-Speed I/O Interface — GigE MAC section
- [Transceiver Basics](../transceivers/transceiver_basics.md) — SerDes architecture
- [Ethernet Cores](../../12_open_source_open_hardware/networking/ethernet_cores.md) — Open-source Ethernet stacks
