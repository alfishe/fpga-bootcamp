[← Gowin Home](../README.md) · [← Section Home](../../README.md)

# Gowin Arora & Arora-V — Mid-Range with Hard Memory Controllers

The mid-range Gowin families spanning 55nm (Arora GW2A) to 22nm (Arora-V GW5A). Add hard DDR2/DDR3/DDR4 controllers, SERDES, and in GW5A, PCIe Gen2.

---

## Specifications

| Feature | Arora GW2A | Arora-V GW5A |
|---|---|---|
| **Process** | 55nm | 22nm |
| **Max LUT4** | 55K (GW2A-55) | 25K (GW5A-25) |
| **Block RAM** | Up to 900 Kb | Up to 810 Kb |
| **DSP** | 16–32 (18×18) | 20–40 (18×18 + mult-add-acc) |
| **Hard Memory Ctrl** | SDR/DDR2/DDR3 (GW2A-18+) | DDR3/LPDDR4 |
| **SERDES** | 4× 2.5 Gbps (GW2A-55) | 4× 6.25 Gbps |
| **PCIe** | None | Gen2 x4 (GW5A-25) |
| **MIPI** | None | D-PHY / MIPI CSI-2 |
| **Boards** | Tang Primer 20K ($40) | Tang Primer 25K ($50) |

---

## When to Upgrade from LittleBee

| Need... | Pick |
|---|---|
| DDR3 memory interface | GW2A-18 or GW5A-25 |
| Transceivers | GW5A-25 (6.25G SERDES) or Cyclone V GX |
| PCIe | GW5A-25 (Gen2 x4) |

---

## Development Boards

### Sipeed (Semi-Official Partner)

| Board | FPGA | LUT4 | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **Tang Primer 20K** | GW2A-LV18PG256 | 20,736 | DDR3 128 MB, HDMI, BLE, microSD, USB-JTAG | ~$40 | Best mid-range Gowin dev board |
| **Tang Primer 25K** | GW5A-LV25MG121 | 23,040 | 22nm, DDR3, 6.25G SERDES ×4, HDMI, USB-JTAG | ~$50 | 22nm Gowin with SERDES |
| Tang Mega 138K | GW5AST-138 | 138,000 | 22nm, PCIe Gen2 ×4, 12.5G SERDES ×4, DDR4, USB 3.0 | ~$150 | High-end Gowin 22nm eval |

### Choosing a Board

| You want... | Get... |
|---|---|
| Best mid-range Gowin development | Tang Primer 20K (~$40) |
| SERDES + PCIe on a budget | Tang Primer 25K (~$50) |
| Higher logic count (GW2A) | Tang Primer 20K (DDR3 capable) |
| Maximum Gowin features | Tang Mega 138K (~$150) |

---

## References

| Source | Path |
|---|---|
| Gowin Semiconductor | https://www.gowinsemi.com |
