[← Intel/Altera Home](../README.md) · [← Section Home](../../README.md)

# Intel Agilex — Chiplet Architecture with AI-Optimized DSP

The current-generation Intel FPGA platform. Agilex abandons monolithic die in favor of **chiplets** (tiles) connected by Intel's EMIB (Embedded Multi-die Interconnect Bridge). Different tiles can use different process nodes — FPGA fabric is on Intel 7 (formerly 10nm), while transceiver and HBM tiles may use different optimized processes.

---

## Family Breakdown

| Family | Series | Position | Process | Max LEs | PCIe | Transceivers | Key Innovation |
|---|---|---|---|---|---|---|---|
| **Agilex 5** | D/E | Entry/mid | Intel 7 | 100K–487K | Gen4 x4/x8 | 17–28 Gbps | Lower cost than Agilex 7, successor to Cyclone V SoC |
| **Agilex 7** | F/I/M | High-perf | Intel 7 | 385K–4,500K+ | Gen4/Gen5 x16 | Up to 58 Gbps | HBM2e, AI-optimized DSP (FP16/BF16/INT8 tensor), direct replacement for Stratix 10 |
| **Agilex 9** | R | RFSoC competitor | Intel 7 + analog die | Base + RF tiles | Gen5 x16 | 58G + direct RF ADCs/DACs | RF data converters, 64 GSPS DAC |

---

## AI DSP Tensor Blocks (Agilex 7/9)

Agilex 7/9 introduces **AI Tensor Blocks** — DSP blocks that process INT8 tensor operations natively:

| Mode | Multiply type | Acc width | Throughput per block |
|---|---|---|---|
| Standard DSP | 18×19 or 27×27 | 48/64-bit | 1–2 mults/cycle |
| FP16 | IEEE 754 half-precision | FP32 accumulation | 1 mult/cycle |
| **INT8 Tensor** | 20× INT8 dot product | 32-bit | **20 INT8 mults/cycle** ≈ 10× INT8 throughput vs standard DSP |

This is Intel's answer to Xilinx Versal's AI Engines, but integrated directly into the DSP blocks rather than a separate compute tile.

---

## EMIB + Chiplet Architecture

```
┌────────────── Agilex 7 M-Series Package ──────────────┐
│                                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ FPGA Tile 1  │  │ FPGA Tile 2  │  │ FPGA Tile 3  │   │
│  │ Intel 7      │  │ Intel 7      │  │ Intel 7      │   │
│  │ 4.5M LEs     │  │ 4.5M LEs     │  │ 4.5M LEs     │   │
│  └──┬───────┬──┘  └──┬───────┬──┘  └──┬───────┬──┘   │
│     │EMIB   │EMIB    │EMIB   │EMIB    │EMIB   │EMIB   │
│  ┌──▼──┐ ┌──▼──────┐ ┌▼──────┐ ┌▼───────────────┐   │
│  │ HBM │ │ XCVR    │ │ PCIe  │ │ HPS Quad A55   │   │
│  │Tile │ │ 112G    │ │ Gen5  │ │ Tile           │   │
│  └─────┘ └─────────┘ └───────┘ └────────────────┘   │
│                                                        │
└────────────────────────────────────────────────────────┘
```

The key advantage: you can mix and match tile configurations. A design needing only moderate logic but lots of transceivers uses a single FPGA tile + large XCVR tile, rather than paying for unused logic capacity.

---

## High-End Generation Comparison

| Criterion | Arria 10 | Stratix 10 | Agilex 7 |
|---|---|---|---|
| **Process** | 20nm | 14nm Tri-Gate | Intel 7 (10nm+) |
| **Max LEs** | 1,150K | 5,510K | 4,500K+ (multi-die) |
| **Max M20K RAM** | 53 Mb | 229 Mb | ~300 Mb |
| **Max DSP** | 1,518 | 5,760 | 4,000+ + tensor |
| **Fastest XCVR** | 28.3 Gbps | 57.8 Gbps | 58 Gbps (PAM4) |
| **PCIe max** | Gen3 x8 | Gen4 x16 | Gen5 x16 |
| **HBM** | No | HBM2 (8 GB) | HBM2e (16 GB+) |
| **Hard FP in DSP** | Yes (FP32) | Yes (FP32) | Yes (FP32/FP16/BF16/INT8) |
| **SoC CPU** | Dual Cortex-A9 | Quad Cortex-A53 | Quad Cortex-A55 (or A76) |
| **Chiplet** | No | No | Yes (EMIB) |
| **Rough cost per LE** | ~$0.0018 | ~$0.0025 | ~$0.0020 |

---

## Best Practices

1. **Agilex 5 D-series is the eventual replacement for Cyclone V SoC** — improved ARM A55 cores, Gen4 PCIe, similar price points.
2. **For >1M LE designs:** Stratix 10 or Agilex 7. Flat-tool timing closure at >1M LEs is the dominant engineering cost — HyperFlex (Stratix) or multi-die constraints (Agilex) save weeks.
3. **Agilex requires Quartus Prime Pro** — not supported in Quartus Prime Lite (free edition). Budget for a license or eval period.

---

## Development Boards

### Intel (First-Party)

| Board | Agilex Variant | LEs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **Agilex 7 FPGA I-Series Dev Kit** | AGIB027R31N (I-Series) | 2,692K | PCIe Gen5 ×16, 58G PAM4 ×12, DDR5, QSFP-DD, FMC+ | ~$15,995 | Gen5 PCIe + DDR5 + PAM4 eval |
| Agilex 7 FPGA M-Series Dev Kit | AGMB027R31N (M-Series) | 2,692K | HBM2e 16 GB, PCIe Gen5 ×16, 58G PAM4, QSFP-DD | ~$19,995 | HBM2e bandwidth + AI tensor DSP eval |
| Agilex 7 FPGA F-Series Dev Kit | AGFA014R24B (F-Series) | 1,437K | PCIe Gen4 ×16, 28G XCVR, DDR4, QSFP28, FMC+ | ~$8,995 | Mid-range Agilex 7 entry |
| **Agilex 5 FPGA D-Series Dev Kit** | A5ED033B (D-Series) | 330K | PCIe Gen4 ×4, 28G XCVR ×8, DDR4, HDMI, FMC | ~$1,495 | Agilex 5 evaluation, Cyclone V SoC successor path |

### Third-Party

| Board | Agilex Variant | LEs | Key Feature | Approx. Price | Best For |
|---|---|---|---|---|---|
| **BittWare IA-860m** | Agilex 7 I-Series | 2,692K | PCIe Gen5 ×16 card, QSFP-DD ×2, DDR5, 100/400G Eth | ~$12,000+ | Datacenter PCIe Gen5 accelerator |
| BittWare IA-440i | Agilex 7 F-Series | 1,437K | PCIe Gen4 ×16, QSFP28 ×4, DDR4 | ~$6,000+ | Lower-cost networking card |

### Choosing a Board

| You want... | Get... |
|---|---|
| Cyclone V SoC successor evaluation | Agilex 5 D-Series Dev Kit (~$1,495) |
| AI tensor DSP + HBM2e | Agilex 7 M-Series Dev Kit |
| PCIe Gen5 development | Agilex 7 I-Series Dev Kit or BittWare IA-860m |
| Mid-range entry to Agilex ecosystem | Agilex 7 F-Series Dev Kit |
| Production deployment | BittWare cards or custom PCB |

---

## References

| Source | Path |
|---|---|
| Agilex 7 FPGA Architecture | Intel FPGA documentation |
| Agilex 5 Product Brief | Intel FPGA documentation |
| Intel EMIB Technology Brief | www.intel.com/emib |
