[← 06 Ip And Cores Home](../README.md) · [← Other Hard Ip Home](README.md) · [← Project Home](../../../README.md)

# Hard Ethernet MACs — Vendor IP Comparison

Most modern FPGAs include hardened Ethernet MAC (Media Access Controller) blocks that handle the MAC-layer framing, pausing, statistics, and PCS interface — eliminating the need for soft-MAC implementations for standard Ethernet rates. This article compares the hard MAC offerings across vendors.

---

## Why Hard MAC Matters

| Metric | Soft MAC (RTL) | Hard MAC (Silicon) |
|---|---|---|
| LUT utilization | 2,000–8,000 LUTs (10G) | 0 LUTs |
| Latency | Variable | Fixed, deterministic |
| Power | 1–3 W (dynamic fabric) | <0.5 W (hardened) |
| Features | Whatever you implement | Vendor-defined (less flexible) |
| Multi-port | Scales linearly in LUTs | Limited by hard block count |

**Decision rule:** Use hard MAC for standard protocols (1G/10G/25G). Use soft MAC only for custom/proprietary MAC-layer protocols.

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
| **SGMII/GbE PCS** | 1.25 Gbps (SGMII) | Serial (DCU) | ECP5 (with DCU) | Hard PCS in serpentdes. Soft MAC on top. |

### Microchip

| IP Block | Rates | Interfaces | Families | Notes |
|---|---|---|---|---|
| **10/100/1000 MAC** | 1G | GMII, RGMII | PolarFire, SmartFusion2 | Soft MAC. ~1.5K LUTs. Good enough for 1G. |
| **XAUI MAC** | 10G | XAUI (4×3.125G) | PolarFire | Hard XAUI PCS + soft MAC. |

---

## Protocol Stack: Where the MAC Sits

```
┌─────────────────────────────┐
│  User Logic (AXI4-Stream)   │ ← Your packet processing
├─────────────────────────────┤
│  MAC (Hard or Soft)         │ ← Framing, address filtering, pause, stats
├─────────────────────────────┤
│  PCS (64B/66B encode)       │ ← Encoding + scrambling
├─────────────────────────────┤
│  PMA (SerDes)               │ ← Serialization
└─────────────────────────────┘
        │
    ────▼────
    RJ45 / SFP / QSFP
```

---

## When to Use Which

| Scenario | Recommended IP |
|---|---|
| Embedded Linux on SoC (Zynq/Cyclone V SoC) | HPS/GEM EMAC — already there, use it |
| 1G copper (RJ45) on FPGA-only chip | TEMAC or Triple-Speed Ethernet + external PHY |
| 10G SFP+ optical | XXVEMAC (Xilinx) or E-Tile (Intel) — hard MAC |
| 25G SFP28 | XXVEMAC (Xilinx) or F-Tile (Intel) |
| 100G QSFP28 | CMAC (Xilinx US+) or E-Tile (Intel S10/Agilex) |
| Custom/proprietary MAC protocol | Soft MAC — full control over framing |

---

## References

- Xilinx PG051: Tri-Mode Ethernet MAC LogiCORE IP
- Xilinx PG318: USXGMII Subsystem
- Xilinx PG203: UltraScale+ 100G Ethernet (CMAC)
- Intel AN 647: Triple-Speed Ethernet IP Core
- Lattice TN1278: ECP5 High-Speed I/O Interface — GigE MAC section
