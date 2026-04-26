[← Intel/Altera Home](../README.md) · [← Section Home](../../README.md)

# Intel Arria 10 — 20nm Mid-Range with High-End IO

Arria 10 is the bridge between Cyclone V and Stratix 10. It delivers 17–28 Gbps transceivers, PCIe Gen3, DDR4, and IEEE 754 hard floating-point DSP at ~60% the cost of Stratix 10. The SoC variant reuses the same dual Cortex-A9 HPS as Cyclone V but clocked to 1.2 GHz.

---

## Specifications

| Feature | Specification |
|---|---|
| **Process** | 20nm |
| **LEs** | 160K–1,150K |
| **ALMs** | 61K–427K |
| **M20K blocks** | 440–2,713 (up to 53 Mb) |
| **DSP blocks** | 312–1,518 (18×19 + 27×27, IEEE 754 hard FP) |
| **Transceivers** | Up to 96× 17.4 Gbps (GX) or 28.3 Gbps (GT) |
| **PCIe** | Gen3 ×8 hard IP + CvP (Configuration via Protocol) |
| **DDR** | Hard DDR4 controller, up to 2,666 Mbps |
| **SoC variant** | Arria 10 SoC — dual Cortex-A9 at 1.2 GHz (same HPS architecture as Cyclone V) |
| **Package** | BGA, up to 1,152 user IOs |

---

## Arria 10 vs Cyclone V SoC

| Criterion | Cyclone V SoC | Arria 10 SoC |
|---|---|---|
| CPU max freq | 925 MHz | 1.2 GHz |
| Fabric LEs | Up to 301K | Up to 660K (SoC); 1,150K (FPGA-only) |
| Transceiver speed | 3–6 Gbps | 17.4–28.3 Gbps |
| PCIe | Gen2 x4 | Gen3 x8 |
| HPS DDR bandwidth | 3.2 GB/s | 4.2 GB/s |
| Interlaken/100G Eth | No | Yes |
| Hard FP DSP | No (integer only) | Yes (IEEE 754 FP32) |
| Open-source flow | No | No |

---

## When Arria 10 Replaces Cyclone V

- Need >300K LEs (Cyclone V ceiling)
- Need 28G transceivers or PCIe Gen3
- Need hard floating-point DSP in fabric (IEEE 754 without ALM overhead)
- Need 100G Ethernet or Interlaken hard IP
- Cyclone V-QoS can't close timing → use newer fabric + better P&R

---

## Development Boards

### Intel (First-Party)

| Board | Arria 10 Variant | LEs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **Arria 10 GX FPGA Dev Kit** | 10AX115S3F45 (GX) | 1,150K | 28 Gbps XCVR ×24, PCIe Gen3 ×8, FMC+, DDR4, QSFP+, 100G Eth | ~$3,495 | Full Arria 10 eval, 28G transceivers + 100G Eth |
| **Arria 10 SoC Dev Kit** | 10AS066K3F40 (SoC) | 660K | Dual Cortex-A9 @ 1.2 GHz, DDR4, PCIe Gen3 ×8, FMC, 28G XCVR | ~$2,995 | SoC development, HPS + high-speed transceiver |

### Third-Party

| Board | Arria 10 Variant | LEs | Key Feature | Approx. Price | Best For |
|---|---|---|---|---|---|
| ReflexCES Arria 10 PCIe | 10AX115 (GX) | 1,150K | PCIe Gen3 ×8 full-height card, DDR4 SODIMM, QSFP28 | ~$2,500+ | Custom PCIe accelerator deployment |

### Choosing a Board

| You want... | Get... |
|---|---|
| Full Arria 10 FPGA evaluation | Arria 10 GX Dev Kit (~$3,495) |
| Arria 10 SoC (HPS + FPGA) | Arria 10 SoC Dev Kit (~$2,995) |
| Production PCIe accelerator card | ReflexCES or custom PCB |
| Cheaper 12G transceiver option | Cyclone 10 GX Dev Kit (~$549) |

---

## References

| Source | Path |
|---|---|
| Arria 10 Device Overview | Intel FPGA documentation |
