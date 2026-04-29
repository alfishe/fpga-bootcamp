[← 12 Open Source Open Hardware Home](../README.md) · [← Litex Home](README.md) · [← Project Home](../../../README.md)

# LiteX Core Ecosystem — LiteDRAM, LiteEth, LitePCIe & More

LiteX's power comes from its ecosystem of "Lite" cores — open-source, vendor-agnostic IP blocks that provide essential SoC functions (DRAM controller, Ethernet MAC, PCIe endpoint, SD card, etc.) with clean Wishbone interfaces.

---

## Core Catalog

| Core | Function | FPGA Families | Resource (approx) | Notes |
|---|---|---|---|---|
| **LiteDRAM** | DDR2/3/4, SDRAM, LPDDR controller | All | 3K–8K LUTs | Auto-calibrating. Supports ECP5, Artix-7, Kintex-7, Cyclone V. |
| **LiteEth** | 10/100/1000 Ethernet MAC + UDP/IP stack | All (with PHY) | 2K–5K LUTs | Hardware UDP/IP stack — ping, ARP, DHCP in gateware. |
| **LitePCIe** | PCIe Gen2 x1/x4/x8 endpoint + DMA | 7-Series, ECP5, Ultrascale+ | 5K–12K LUTs | Uses hard PCIe block. Wishbone-to-PCIe bridge. |
| **LiteSATA** | SATA Gen1/2 host controller | 7-Series, ECP5 | 3K–6K LUTs | Uses transceivers. SATA II 3 Gbps. |
| **LiteSDCard** | SD/SDHC card SPI/SD-mode controller | All | ~500 LUTs | Boot from SD. File system not included (BIOS handles raw reads). |
| **LiteSPI** | QSPI/Dual/Octal SPI flash controller | All | ~400 LUTs | For flash memory access |
| **LiteICLink** | Inter-FPGA high-speed serial link | 7-Series, ECP5 | 1K–3K LUTs | Uses transceivers. Simple point-to-point. |
| **LiteScope** | On-chip logic analyzer | All | 2K–6K LUTs | Like ILA/SignalTap but open-source. Trigger, capture, UART dump. |

---

## LiteDRAM Deep Dive

LiteDRAM is arguably LiteX's most important core. It auto-calibrates at every boot:

1. **Write leveling** — aligns DQS to clock per byte lane
2. **Read leveling** — adjusts per-bit delays to center DQ in data eye
3. **Memtest** — writes/reads pattern to verify calibration

**Compatibility:**
| FPGA | DDR Type | Status |
|---|---|---|
| Artix-7 / Kintex-7 | DDR3 | ✅ Mature |
| Kintex Ultrascale+ | DDR4 | ✅ Mature |
| ECP5 | SDRAM | ✅ Mature |
| ECP5 | DDR3 | ⚠️ Experimental |
| Cyclone V | SDRAM / DDR3 | ⚠️ Limited testing |

---

## LiteEth — Hardware UDP/IP Stack

LiteEth includes a hardware TCP/UDP/IP stack, meaning your FPGA can respond to ping, DHCP, and ARP without a soft CPU:

```python
# Add Ethernet to your LiteX SoC
soc = BaseSoC(with_ethernet=True, eth_ip="192.168.1.50")

# UDP echo server runs in gateware — no CPU needed
# Python test: socket.sendto(b"hello", ("192.168.1.50", 1234))
```

---

## Best Practices

1. **LiteDRAM: Start with SDRAM on ECP5** — DDR3 support is experimental, SDRAM is rock-solid
2. **LiteEth: Use for lightweight UDP** — not a replacement for full TCP stack (use soft CPU for that)
3. **LitePCIe: Verify link training first** — same debugging approach as vendor PCIe (LTSSM, equalization)
4. **Pin constraints matter** — LiteDRAM needs correct pin grouping just like MIG/EMIF

---

## References

- [LiteDRAM GitHub](https://github.com/enjoy-digital/litedram)
- [LiteEth GitHub](https://github.com/enjoy-digital/liteeth)
- [LitePCIe GitHub](https://github.com/enjoy-digital/litepcie)
